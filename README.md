# Urbanización La Querencia - Dashboard MVP

Aplicación Streamlit para análisis de egresos de urbanización.

## Características

- 📊 **Overview**: Ritmo y control del gasto con narrativa automática
- 📑 **Conceptos**: Análisis detallado por conceptos
- 🏢 **Proveedores**: Análisis de concentración de proveedores
- ⚠️ **Anomalías**: Detección de meses y pólizas atípicas
- 🔍 **Explorer**: Explorador interactivo de pólizas

## Requisitos

- Python 3.8+
- Streamlit
- pandas
- numpy
- openpyxl
- altair

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
streamlit run app.py
```

## Estructura

```
laquerencia_urbanizacion_app/
├── app.py                 # Página principal
├── utils.py               # Funciones de utilidad
├── requirements.txt       # Dependencias
└── pages/
    ├── 01_Overview.py     # Resumen general
    ├── 02_Conceptos.py    # Análisis por conceptos
    ├── 03_Proveedores.py  # Análisis por proveedores
    ├── 04_Anomalias.py    # Detección de anomalías
    └── 05_Explorer.py     # Explorador de datos
```

## Formato de Datos

El archivo Excel debe contener las siguientes columnas:
- Mes
- Número
- Fecha
- Póliza
- Concepto
- Proveedor
- Monto
- Categoría
- Concepto Russildi
