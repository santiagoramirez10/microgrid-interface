from pathlib import Path
import shutil
from typing import Any, Set, Dict

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

import pandas as pd
import numpy as np

# Librería de dimensionamiento
from sizingmicrogrids.utilities import (
    read_data,
    calculate_cost_data,
    read_multiyear_data,
    calculate_multiyear_data,
)
from sizingmicrogrids.classes import RandomCreate
import sizingmicrogrids.mainfunctions as mf


# ---------------------------------------------------------------------
# Rutas base
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
AUX_DIR = BASE_DIR / "auxiliar"
UPLOAD_DIR = BASE_DIR / "tmp_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

FISCAL_PATH = AUX_DIR / "fiscal_incentive.json"
COST_PATH = AUX_DIR / "parameters_cost.json"
MYEAR_PATH = AUX_DIR / "multiyear.json"


# ---------------------------------------------------------------------
# App FastAPI + CORS
# ---------------------------------------------------------------------

app = FastAPI(title="Sizing Microgrids API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
        "http://127.0.0.1:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def save_upload(file: UploadFile) -> Path:
    """Guarda un archivo subido en tmp_uploads y devuelve la ruta."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Archivo sin nombre.")
    dest = UPLOAD_DIR / file.filename
    with dest.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return dest


def df_to_records(obj: Any):
    """
    Convierte DataFrames en listas de diccionarios, limpiando NaN/Inf
    para que el JSON sea válido.
    """
    if obj is None:
        return []
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, pd.DataFrame):
        cleaned = obj.replace([np.inf, -np.inf], np.nan).fillna(0)
        return cleaned.reset_index(drop=True).to_dict(orient="records")
    return obj


def snapshot_folder() -> Set[str]:
    """Devuelve el conjunto de nombres de archivo actualmente en UPLOAD_DIR."""
    return {p.name for p in UPLOAD_DIR.iterdir() if p.is_file()}


def build_summary_from_excels() -> Dict[str, float]:
    """
    Lee los Excels presentes en tmp_uploads y construye un resumen con:

    - lcoe
    - area
    - lpsp_mean
    - mean_surplus
    - mean_diesel_generation
    - mean_eolic_generation
    - mean_solar_generation
    - mean_batteries_generation
    """
    summary: Dict[str, float] = {}

    all_files = snapshot_folder()
    excel_files = {f for f in all_files if f.lower().endswith((".xlsx", ".xls"))}
    if not excel_files:
        return summary

    labels_map = {
        "lcoe": "lcoe",
        "area": "area",
        "lpsp mean": "lpsp_mean",
        "mean surplus": "mean_surplus",
        "mean diesel generation": "mean_diesel_generation",
        "mean eolic generation": "mean_eolic_generation",
        "mean solar generation": "mean_solar_generation",
        "mean batteries generation": "mean_batteries_generation",
    }

    for fname in excel_files:
        fpath = UPLOAD_DIR / fname
        if not fpath.exists():
            continue

        try:
            df = pd.read_excel(fpath, header=None)
        except Exception:
            continue

        if df.empty or df.shape[1] < 2:
            continue

        for _, row in df.iterrows():
            label_raw = row.iloc[0]
            if pd.isna(label_raw):
                continue
            label = str(label_raw).strip().lower()
            if label in labels_map:
                key = labels_map[label]
                value = row.iloc[1]
                if not pd.isna(value):
                    summary[key] = float(value)

        if "lcoe" in summary and "area" in summary:
            break

    return summary


# ---------------------------------------------------------------------
# Endpoints generales
# ---------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/download/{filename}")
def download(filename: str):
    """Devuelve un archivo generado por el modelo."""
    path = UPLOAD_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    suffix = path.suffix.lower()
    media_type = "application/octet-stream"

    if suffix in [".html", ".htm"]:
        media_type = "text/html"
    elif suffix == ".png":
        media_type = "image/png"
    elif suffix in [".jpg", ".jpeg"]:
        media_type = "image/jpeg"
    elif suffix in [".xlsx", ".xls"]:
        media_type = (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    return FileResponse(path, filename=filename, media_type=media_type)


# ---------------------------------------------------------------------
# 1) MODELO DETERMINISTA (1 AÑO)
# ---------------------------------------------------------------------

@app.post("/optimize/deterministic")
async def optimize_deterministic(
    instance_file: UploadFile = File(...),
    parameters_file: UploadFile = File(...),
    demand_file: UploadFile = File(...),
    forecast_file: UploadFile = File(...),

    years: int = Form(20),
    demand_covered: float = Form(0.6),
    discount_rate: float = Form(0.08),
    lpsp_limit: int = Form(10),
):
    """
    Ejecuta el modelo determinístico (1 año) con los 4 archivos de una ZNI.
    """

    # Guardar archivos subidos
    instance_path = save_upload(instance_file)
    params_path = save_upload(parameters_file)
    demand_path = save_upload(demand_file)
    forecast_path = save_upload(forecast_file)

    if not FISCAL_PATH.exists() or not COST_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=(
                "No se encuentran los archivos auxiliares "
                "fiscal_incentive.json o parameters_cost.json"
            ),
        )

    (
        demand_df,
        forecast_df,
        generators,
        batteries,
        instance_data,
        fisc_data,
        cost_data,
    ) = read_data(
        str(demand_path),
        str(forecast_path),
        str(params_path),
        str(instance_path),
        str(FISCAL_PATH),
        str(COST_PATH),
    )

    instance_data["years"] = int(years)
    instance_data["demand_covered"] = float(demand_covered)
    instance_data["i_f"] = float(discount_rate)
    instance_data["tlpsp"] = int(lpsp_limit)

    generators, batteries = calculate_cost_data(
        generators, batteries, instance_data, cost_data
    )
    demand_df["demand"] = instance_data["demand_covered"] * demand_df["demand"]

    ADD_FUNCTION = "GRASP"
    REMOVE_FUNCTION = "RANDOM"
    rand_ob = RandomCreate(seed=None)
    best_nsh = 0
    folder_path = str(UPLOAD_DIR)

    percent_df, energy_df, renew_df, total_df, brand_df = mf.maindispatch(
        demand_df,
        forecast_df,
        generators,
        batteries,
        instance_data,
        fisc_data,
        cost_data,
        best_nsh,
        rand_ob,
        ADD_FUNCTION,
        REMOVE_FUNCTION,
        folder_path,
    )

    # Copiar temp-plot.html a tmp_uploads si existe
    temp_plot = BASE_DIR / "temp-plot.html"
    if temp_plot.exists():
        shutil.copyfile(temp_plot, UPLOAD_DIR / "temp-plot.html")

    all_files = snapshot_folder()
    input_files = {
        instance_path.name,
        params_path.name,
        demand_path.name,
        forecast_path.name,
    }
    reports = sorted(f for f in all_files if f not in input_files)

    summary = build_summary_from_excels()

    result = {
        "message": "Modelo determinístico ejecutado correctamente.",
        "summary": summary,
        "percent": df_to_records(percent_df),
        "energy": df_to_records(energy_df),
        "renew": df_to_records(renew_df),
        "total": df_to_records(total_df),
        "brand": df_to_records(brand_df),
        "instance_data_used": instance_data,
        "reports": reports,
    }

    return result


# ---------------------------------------------------------------------
# 2) MODELO MULTIYEAR
# ---------------------------------------------------------------------

@app.post("/optimize/multiyear")
async def optimize_multiyear(
    instance_file: UploadFile = File(...),
    parameters_file: UploadFile = File(...),
    demand_file: UploadFile = File(...),
    forecast_file: UploadFile = File(...),

    years: int = Form(20),
    demand_covered: float = Form(0.6),
    discount_rate: float = Form(0.08),
    lpsp_limit: int = Form(10),
):
    """
    Ejecuta el modelo multiyear con los 4 archivos de una ZNI.
    """

    instance_path = save_upload(instance_file)
    params_path = save_upload(parameters_file)
    demand_path = save_upload(demand_file)
    forecast_path = save_upload(forecast_file)

    if not (FISCAL_PATH.exists() and COST_PATH.exists() and MYEAR_PATH.exists()):
        raise HTTPException(
            status_code=500,
            detail=(
                "No se encuentran los archivos auxiliares necesarios "
                "(fiscal_incentive.json, parameters_cost.json, multiyear.json)"
            ),
        )

    (
        demand_df_i,
        forecast_df_i,
        generators,
        batteries,
        instance_data,
        fisc_data,
        cost_data,
        my_data,
    ) = read_multiyear_data(
        str(demand_path),
        str(forecast_path),
        str(params_path),
        str(instance_path),
        str(FISCAL_PATH),
        str(COST_PATH),
        str(MYEAR_PATH),
    )

    instance_data["years"] = int(years)
    instance_data["demand_covered"] = float(demand_covered)
    instance_data["i_f"] = float(discount_rate)
    instance_data["tlpsp"] = int(lpsp_limit)

    demand_df_i["demand"] = instance_data["demand_covered"] * demand_df_i["demand"]
    generators, batteries = calculate_cost_data(
        generators, batteries, instance_data, cost_data
    )

    demand_df, forecast_df = calculate_multiyear_data(
        demand_df_i, forecast_df_i, my_data, instance_data["years"]
    )

    ADD_FUNCTION = "GRASP"
    REMOVE_FUNCTION = "RANDOM"
    rand_ob = RandomCreate(seed=None)
    best_nsh = 0
    folder_path = str(UPLOAD_DIR)

    percent_df, energy_df, renew_df, total_df, brand_df = mf.maindispatchmy(
        demand_df,
        forecast_df,
        generators,
        batteries,
        instance_data,
        fisc_data,
        cost_data,
        my_data,
        best_nsh,
        rand_ob,
        ADD_FUNCTION,
        REMOVE_FUNCTION,
        folder_path,
    )

    temp_plot = BASE_DIR / "temp-plot.html"
    if temp_plot.exists():
        shutil.copyfile(temp_plot, UPLOAD_DIR / "temp-plot.html")

    all_files = snapshot_folder()
    input_files = {
        instance_path.name,
        params_path.name,
        demand_path.name,
        forecast_path.name,
    }
    reports = sorted(f for f in all_files if f not in input_files)

    summary = build_summary_from_excels()

    result = {
        "message": "Modelo multiyear ejecutado correctamente.",
        "summary": summary,
        "percent": df_to_records(percent_df),
        "energy": df_to_records(energy_df),
        "renew": df_to_records(renew_df),
        "total": df_to_records(total_df),
        "brand": df_to_records(brand_df),
        "instance_data_used": instance_data,
        "reports": reports,
    }

    return result
