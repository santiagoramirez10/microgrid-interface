# Dimensionador de Microrredes Aisladas — Interfaz Web

Este repositorio contiene el desarrollo completo de una herramienta web para el dimensionamiento de microrredes aisladas, integrando una interfaz gráfica moderna con el modelo computacional implementado originalmente en Python por el grupo SENECA de la Universidad de Antioquia.
La plataforma combina:

- Frontend en **Angular**
- Backend en **FastAPI (Python)**
- Algoritmo de optimización escrito en **Pyomo**
- Visualización de resultados energéticos y económicos
- Carga validada de archivos **CSV y JSON**

El propósito es ofrecer una herramienta accesible tanto para usuarios sin experiencia en programación como para investigadores y estudiantes que deseen extender o adaptar el modelo.

---

# 1. Contenido del repositorio

La estructura exacta del proyecto es la siguiente:

```
microgrid-interface/
│
├── backend/
│   └── microgrid-api/
│       ├── auxiliar/                
│       ├── sizingmicrogrids/        
│       │   ├── classes.py
│       │   ├── mainfunctions.py
│       │   ├── operators.py
│       │   ├── opt.py
│       │   ├── strategies.py
│       │   ├── utilities.py
│       │   └── data/                
│       │
│       ├── tmp_uploads/             
│       ├── main.py                  
│       ├── requirements.txt
│       └── temp-plot.html           
│
├── frontend/
│   └── microrred-app/
│       ├── src/
│       │   ├── app/
│       │   │   ├── pages/           
│       │   │   ├── components/      
│       │   │   ├── services/        
│       │   │   └── models/          
│       │   ├── assets/              
│       │   └── environments/
│       ├── angular.json
│       ├── package.json
│       └── README.md
│
├── docs/
│   ├── Wireframes/
│   │   ├── design_A_tabs/
│   │   ├── design_B_sidebar/
│   │   ├── design_C_cards/
│   │   └── design_D_steps/
│   │
│   ├── manual_programadores.pdf
│   ├── manual_usuarios.pdf
│   ├── manual_original_dimensionador.pdf
│   ├── informe_proyecto.pdf
│   └── anexos/
│
└── README.md
```

---

# 2. Descripción general del sistema

El sistema permite cargar archivos de la microrred (instancia, parámetros, demanda y clima), ejecutar el modelo matemático y mostrar los resultados de manera organizada y visual.

### Flujo:
1. El usuario carga los cuatro archivos requeridos.
2. El frontend valida y envía los datos al backend.
3. FastAPI los almacena temporalmente y ejecuta el modelo Pyomo.
4. El modelo determina capacidades óptimas, costos, generación y métricas.
5. Angular presenta los resultados mediante tablas y gráficos.

---

# 3. Ejecución local (modo programador)

## Backend

```bash
cd backend/microgrid-api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Disponible en:  
**http://localhost:8000**

---

## Frontend

```bash
cd frontend/microrred-app
npm install
ng serve --open
```

Disponible en:  
**http://localhost:4200**

---

# 4. Modelo de dimensionamiento

El motor de optimización (carpeta `sizingmicrogrids/`) está basado en el artículo:

Castellanos-Buitrago, S., Maya-Duque, P., Villa-Acevedo, W., Muñoz-Galeano, N., & López-Lezama, J.  
“Enhancing Energy Microgrid Sizing: A Multiyear Optimization Approach with Uncertainty Considerations for Optimal Design”, *Algorithms*, 2025.

Repositorio original del modelo:  
https://github.com/SENECA-UDEA/microgrids_sizing

---

# 5. Documentación incluida

En `/docs/` se encuentran:

- Manual para programadores  
- Manual para usuarios sin conocimientos técnicos  
- Manual original del dimensionador  
- Informe completo del proyecto  
- Anexos, capturas, wireframes y evidencias  

---

# 6. Submódulo institucional

Este repositorio se encuentra agregado como submódulo dentro del repositorio del Departamento de Ingeniería Eléctrica de la Universidad de Antioquia, con el fin de permitir consulta académica, evaluación del código y revisión del desarrollo.

Submódulo:  
https://github.com/santiagoramirez10/microgrid-interface

---

# 7. Enlaces importantes

- Interfaz desarrollada (este repositorio):  
  https://github.com/santiagoramirez10/microgrid-interface  

- Modelo original del dimensionador:  
  https://github.com/SENECA-UDEA/microgrids_sizing  

---

# 8. Licencia
Proyecto académico de la Facultad de Ingeniería, Universidad de Antioquia.  
Uso para investigación, formación y desarrollo académico.
