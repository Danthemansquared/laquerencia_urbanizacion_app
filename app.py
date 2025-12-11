import streamlit as st
import pandas as pd
from utils import load_data, format_millions

st.set_page_config(
    page_title="Urbanización La Querencia",
    layout="wide",
)

st.title("Urbanización La Querencia – Dashboard MVP")

st.markdown(
    """
Esta app te ayuda a analizar los **egresos de urbanización** a partir de tu archivo de Excel
ya curado (donde tú llenas *Categoría* y *Concepto Russildi*).

1. Sube el archivo de egresos.
2. Usa las pestañas de arriba para explorar: Overview, Conceptos, Proveedores, Anomalías y Explorer.
"""
)

uploaded_file = st.file_uploader("Sube el archivo de Urbanización (Excel)", type=["xlsx"])

if uploaded_file is not None:
    try:
        # Guardar una copia del dataframe original para diagnóstico
        df_raw = pd.read_excel(uploaded_file)
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

        st.dataframe(
            df.head(20),
            use_container_width=True,
        )
        st.info(
            "Puedes navegar a las otras páginas desde el menú lateral (multipage) o el menú superior dependiendo de tu configuración."
        )
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
else:
    st.info("Sube un archivo para comenzar.")