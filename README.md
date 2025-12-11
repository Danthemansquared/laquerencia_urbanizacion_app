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

## Carga Automática de Datos

La aplicación soporta carga automática de datos desde una URL, lo que permite compartir el enlace de la aplicación sin que los usuarios tengan que cargar el archivo manualmente.

### Opción 1: Configurar URL por defecto (Streamlit Cloud)

Si estás desplegando en Streamlit Cloud:

1. Ve a tu aplicación en Streamlit Cloud
2. Click en "Settings" → "Secrets"
3. Agrega la siguiente configuración:

```toml
DEFAULT_DATA_URL = "https://drive.google.com/uc?export=download&id=TU_FILE_ID"
```

**Para Google Drive:**
- Sube tu archivo Excel a Google Drive
- Click derecho → Compartir → Cambiar a "Cualquiera con el enlace"
- Copia el ID del archivo de la URL (la parte después de `/d/` y antes del siguiente `/`)
- Usa el formato: `https://drive.google.com/uc?export=download&id=TU_FILE_ID`

### Opción 2: Configurar URL localmente

Crea un archivo `.streamlit/secrets.toml` en la raíz del proyecto:

```toml
DEFAULT_DATA_URL = "https://drive.google.com/uc?export=download&id=TU_FILE_ID"
```

**Nota:** El archivo `.streamlit/secrets.toml` está en `.gitignore` y no se subirá al repositorio.

### Opción 3: Usar la interfaz de la aplicación

1. Abre la aplicación
2. Ve a la pestaña "🔗 Cargar desde URL"
3. Pega la URL de tu archivo
4. Click en "💾 Guardar como predeterminada" para que se cargue automáticamente en futuras sesiones

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
