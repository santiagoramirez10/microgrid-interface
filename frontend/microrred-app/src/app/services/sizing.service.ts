import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

export type OptimizationMode = 'deterministic' | 'multiyear';

export interface BackendSummary {
  // Campos que ya tenías
  totalEnergy?: number | null;
  lcoe?: number | null;
  area?: number | null;
  notServedHours?: number | null;

  // Campos nuevos para la tabla de resultados
  lpsp_mean?: number | null;
  mean_surplus?: number | null;
  mean_diesel_generation?: number | null;
  mean_eolic_generation?: number | null;
  mean_solar_generation?: number | null;
  mean_batteries_generation?: number | null;
}

export interface BackendResult {
  message: string;
  summary?: BackendSummary;
  percent: any[];
  energy: any[];
  renew: any[];
  total: any[];
  brand: any[];
  reports?: string[]; // nombres de archivos generados (excel, imágenes, etc.)
}

export interface FilePayload {
  instance: File;
  parameters: File;
  demand: File;
  forecast: File;
}

export interface ExtraOptions {
  years?: number;
  demandCovered?: number;
  discountRate?: number; // i_f
  lpspLimit?: number;    // tlpsp
}

@Injectable({
  providedIn: 'root',
})
export class SizingService {
  private readonly baseUrl = 'http://127.0.0.1:8000';

  constructor(private http: HttpClient) {}

  getDownloadUrl(filename: string): string {
    return `${this.baseUrl}/download/${encodeURIComponent(filename)}`;
  }

  runOptimization(
    mode: OptimizationMode,
    files: FilePayload,
    options?: ExtraOptions
  ) {
    const formData = new FormData();
    formData.append('instance_file', files.instance);
    formData.append('parameters_file', files.parameters);
    formData.append('demand_file', files.demand);
    formData.append('forecast_file', files.forecast);

    if (options?.years != null) {
      formData.append('years', String(options.years));
    }
    if (options?.demandCovered != null) {
      formData.append('demand_covered', String(options.demandCovered));
    }
    if (options?.discountRate != null) {
      formData.append('discount_rate', String(options.discountRate));
    }
    if (options?.lpspLimit != null) {
      formData.append('lpsp_limit', String(options.lpspLimit));
    }

    const endpoint =
      mode === 'deterministic'
        ? `${this.baseUrl}/optimize/deterministic`
        : `${this.baseUrl}/optimize/multiyear`;

    return this.http.post<BackendResult>(endpoint, formData);
  }
}
