import streamlit as st
import pandas as pd
import requests
import io
from utils import load_data, load_data_from_url, format_millions

st.set_page_config(
    page_title="Urbanización La Querencia",
    layout="wide",
)

st.title("Urbanización La Querencia – Dashboard MVP")

st.markdown(
    """
Esta app te ayuda a analizar los **egresos de urbanización** a partir de tu archivo de Excel
ya curado (donde tú llenas *Categoría* y *Concepto Russildi*).
"""
)

st.caption("💡 **Tip:** Sube el archivo de egresos o proporciona una URL. Usa las pestañas de arriba para explorar: Overview, Conceptos, Proveedores, Anomalías y Explorer.")

# Intentar cargar automáticamente desde URL si está configurada
auto_load_url = None
try:
    if hasattr(st, 'secrets'):
        auto_load_url = st.secrets.get("DEFAULT_DATA_URL", None)
except (FileNotFoundError, AttributeError, KeyError):
    # Si no existe secrets.toml, simplemente continuar sin URL automática
    pass

if not auto_load_url and "data_url" in st.session_state and st.session_state["data_url"]:
    auto_load_url = st.session_state["data_url"]

# Cargar automáticamente si hay URL y no hay datos cargados
if (auto_load_url and ("df" not in st.session_state or st.session_state.get("df") is None)):
    try:
        with st.spinner("🔄 Cargando datos automáticamente desde URL..."):
            df = load_data_from_url(auto_load_url)
            st.session_state["df"] = df
            
            # Guardar también el raw para diagnóstico
            response = requests.get(auto_load_url, timeout=30)
            response.raise_for_status()
            df_raw = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
            st.session_state["df_raw"] = df_raw
            st.session_state["data_url"] = auto_load_url
            
            st.success("✅ Datos cargados automáticamente")
            st.rerun()  # Recargar para mostrar los datos
    except Exception as e:
        st.warning(f"⚠️ No se pudo cargar automáticamente: {str(e)}")

# Opciones de carga
tab1, tab2 = st.tabs(["📁 Subir archivo", "🔗 Cargar desde URL"])

uploaded_file = None
load_from_url = False

with tab1:
    uploaded_file = st.file_uploader("Sube el archivo de Urbanización (Excel)", type=["xlsx"])

with tab2:
    with st.container():
        st.markdown("#### 📋 Carga desde URL")
        st.caption("Puedes compartir un enlace a tu archivo Excel desde Google Drive, Google Sheets, Dropbox o cualquier servidor web.")
        
        with st.expander("ℹ️ Instrucciones detalladas", expanded=False):
            st.markdown("""
            **Para Google Sheets:**
            1. Abre tu hoja de cálculo en Google Sheets
            2. Click en "Compartir" → Cambiar a "Cualquiera con el enlace"
            3. Copia el enlace completo (se convertirá automáticamente a Excel)
            
            **Para Google Drive (archivos .xlsx):**
            1. Sube tu archivo Excel a Google Drive
            2. Click derecho → Compartir → Cambiar a "Cualquiera con el enlace"
            3. Copia el enlace completo
            """)
    
    # Obtener URL por defecto de forma segura
    default_url = st.session_state.get("data_url", "")
    try:
        if hasattr(st, 'secrets'):
            default_url = st.secrets.get("DEFAULT_DATA_URL", default_url)
    except (FileNotFoundError, AttributeError, KeyError):
        pass
    
    data_url = st.text_input(
        "URL del archivo Excel",
        value=default_url,
        help="Pega la URL completa del archivo Excel o Google Sheets",
        placeholder="https://docs.google.com/spreadsheets/d/... o https://drive.google.com/file/d/..."
    )
    
    col_url1, col_url2 = st.columns([3, 1])
    with col_url1:
        if data_url and st.button("🔄 Cargar desde URL", type="primary", use_container_width=True):
            load_from_url = True
    with col_url2:
        if st.session_state.get("data_url"):
            if st.button("💾 Guardar como predeterminada", use_container_width=True):
                st.session_state["data_url"] = data_url
                st.success("URL guardada. Se cargará automáticamente en futuras sesiones.")

# Procesar carga desde URL
if load_from_url and data_url:
    try:
        with st.spinner("Cargando datos desde URL..."):
            df = load_data_from_url(data_url)
            st.session_state["df"] = df
            
            # Guardar también el raw para diagnóstico
            response = requests.get(data_url, timeout=30)
            response.raise_for_status()
            df_raw = pd.read_excel(io.BytesIO(response.content), engine='openpyxl')
            st.session_state["df_raw"] = df_raw
            st.session_state["data_url"] = data_url
            
            st.success("✅ Archivo cargado correctamente desde URL")
            st.rerun()
    except Exception as e:
        st.error(f"Error al cargar desde URL: {e}")
        st.info("Verifica que la URL sea accesible públicamente y que el archivo sea válido.")

# Procesar carga desde archivo
if uploaded_file is not None:
    try:
        # Guardar una copia del dataframe original para diagnóstico
        df_raw = pd.read_excel(uploaded_file, engine='openpyxl')
        st.session_state["df_raw"] = df_raw
        
        df = load_data(uploaded_file)
        st.session_state["df"] = df

        st.success("Archivo cargado correctamente ✅")

        # Mini resumen rápido
        total_monto = df["Monto"].sum()
        years = sorted(df["Año"].dropna().unique())
        meses = sorted(df["MesNum"].dropna().unique())
        
        # Diagnóstico: contar por mes
        from utils import MONTH_NAMES
        conteo_por_mes = df.groupby("MesNum").size()
        meses_con_datos = {MONTH_NAMES.get(m, str(m)): int(conteo) for m, conteo in conteo_por_mes.items()}

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Total histórico en archivo", format_millions(total_monto))
        with c2:
            st.metric("Años incluidos", ", ".join(str(y) for y in years) if len(years) > 0 else "N/A")
        with c3:
            st.metric("Meses distintos", len(meses))
        
        # Mostrar conteo por mes
        with st.expander("📊 Diagnóstico: Movimientos por mes", expanded=True):
            st.write("**Conteo de movimientos por mes (cargados exitosamente):**")
            # Ordenar por número de mes
            meses_ordenados = sorted(meses_con_datos.items(), key=lambda x: next((k for k, v in MONTH_NAMES.items() if v == x[0]), 999))
            for mes_nombre, conteo in meses_ordenados:
                st.write(f"- {mes_nombre}: {conteo} movimientos")
            
            # Análisis de meses faltantes
            meses_esperados = set(MONTH_NAMES.values())
            meses_encontrados = set(meses_con_datos.keys())
            meses_faltantes = meses_esperados - meses_encontrados
            
            if meses_faltantes:
                st.warning(f"⚠️ **Meses no encontrados en los datos cargados:** {sorted(meses_faltantes)}")
                
                # Analizar el archivo original para ver qué hay
                if "df_raw" in st.session_state:
                    df_raw = st.session_state["df_raw"]
                    
                    # Mostrar valores únicos en columna Mes del archivo original
                    meses_raw = df_raw["Mes"].astype(str).str.strip().str.capitalize().unique()
                    meses_raw_clean = sorted([m for m in meses_raw if m.lower() != 'nan'])
                    st.write(f"**Valores únicos en columna 'Mes' del archivo original:** {meses_raw_clean}")
                    
                    # Contar registros por mes en el archivo original
                    st.write("**Conteo en archivo original (antes de filtros):**")
                    conteo_raw = df_raw["Mes"].astype(str).str.strip().str.capitalize().value_counts().sort_index()
                    for mes_raw, count in conteo_raw.items():
                        if mes_raw.lower() != 'nan':
                            # Verificar si se mapeó correctamente
                            from utils import MONTH_MAP
                            mes_normalizado = mes_raw.strip().capitalize()
                            mapeado = MONTH_MAP.get(mes_normalizado, "NO MAPEADO")
                            status = "✅" if mapeado != "NO MAPEADO" else "❌"
                            st.write(f"- {status} {mes_raw}: {count} registros → {mapeado if mapeado != 'NO MAPEADO' else 'NO RECONOCIDO'}")

        with st.container():
            st.subheader("📊 Vista previa de datos")
            st.caption(f"Mostrando los primeros 20 registros de {len(df)} totales")
            st.dataframe(
                df.head(20),
                use_container_width=True,
            )
        
        st.info(
            "💡 Puedes navegar a las otras páginas desde el menú lateral (multipage) o el menú superior dependiendo de tu configuración."
        )
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")

# Mostrar datos si ya están cargados (desde URL automática o previa)
elif "df" in st.session_state and st.session_state.get("df") is not None:
    df = st.session_state["df"]
    
    # Mostrar indicador de que los datos están cargados
    if st.session_state.get("data_url"):
        st.success(f"✅ Datos cargados desde URL (se cargarán automáticamente al compartir el enlace)")
        if st.button("🔄 Recargar datos"):
            try:
                with st.spinner("Recargando..."):
                    df = load_data_from_url(st.session_state["data_url"])
                    st.session_state["df"] = df
                    st.rerun()
            except Exception as e:
                st.error(f"Error al recargar: {e}")
    
    # Mini resumen rápido
    total_monto = df["Monto"].sum()
    years = sorted(df["Año"].dropna().unique())
    meses = sorted(df["MesNum"].dropna().unique())
    
    # Diagnóstico: contar por mes
    from utils import MONTH_NAMES
    conteo_por_mes = df.groupby("MesNum").size()
    meses_con_datos = {MONTH_NAMES.get(m, str(m)): int(conteo) for m, conteo in conteo_por_mes.items()}

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total histórico en archivo", format_millions(total_monto))
    with c2:
        st.metric("Años incluidos", ", ".join(str(y) for y in years) if len(years) > 0 else "N/A")
    with c3:
        st.metric("Meses distintos", len(meses))
    
    # Mostrar conteo por mes
    with st.expander("📊 Diagnóstico: Movimientos por mes", expanded=False):
        st.write("**Conteo de movimientos por mes (cargados exitosamente):**")
        # Ordenar por número de mes
        meses_ordenados = sorted(meses_con_datos.items(), key=lambda x: next((k for k, v in MONTH_NAMES.items() if v == x[0]), 999))
        for mes_nombre, conteo in meses_ordenados:
            st.write(f"- {mes_nombre}: {conteo} movimientos")
        
        # Análisis de meses faltantes
        meses_esperados = set(MONTH_NAMES.values())
        meses_encontrados = set(meses_con_datos.keys())
        meses_faltantes = meses_esperados - meses_encontrados
        
        if meses_faltantes:
            st.warning(f"⚠️ **Meses no encontrados en los datos cargados:** {sorted(meses_faltantes)}")
            
            # Analizar el archivo original para ver qué hay
            if "df_raw" in st.session_state:
                df_raw = st.session_state["df_raw"]
                
                # Mostrar valores únicos en columna Mes del archivo original
                meses_raw = df_raw["Mes"].astype(str).str.strip().str.capitalize().unique()
                meses_raw_clean = sorted([m for m in meses_raw if m.lower() != 'nan'])
                st.write(f"**Valores únicos en columna 'Mes' del archivo original:** {meses_raw_clean}")
                
                # Contar registros por mes en el archivo original
                st.write("**Conteo en archivo original (antes de filtros):**")
                conteo_raw = df_raw["Mes"].astype(str).str.strip().str.capitalize().value_counts().sort_index()
                for mes_raw, count in conteo_raw.items():
                    if mes_raw.lower() != 'nan':
                        # Verificar si se mapeó correctamente
                        from utils import MONTH_MAP
                        mes_normalizado = mes_raw.strip().capitalize()
                        mapeado = MONTH_MAP.get(mes_normalizado, "NO MAPEADO")
                        status = "✅" if mapeado != "NO MAPEADO" else "❌"
                        st.write(f"- {status} {mes_raw}: {count} registros → {mapeado if mapeado != 'NO MAPEADO' else 'NO RECONOCIDO'}")

    with st.container():
        st.subheader("📊 Vista previa de datos")
        st.caption(f"Mostrando los primeros 20 registros de {len(df)} totales")
        st.dataframe(
            df.head(20),
            use_container_width=True,
        )
    
    st.info(
        "💡 Puedes navegar a las otras páginas desde el menú lateral (multipage) o el menú superior dependiendo de tu configuración."
    )
else:
    st.info("👆 Sube un archivo o proporciona una URL para comenzar.")