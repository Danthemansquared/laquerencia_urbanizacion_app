import streamlit as st
import pandas as pd
from utils import ensure_data_loaded, apply_global_filters

st.set_page_config(layout="wide")

def main():
    ensure_data_loaded()
    df = st.session_state["df"]

    st.title("Explorador de pólizas")

    filtered = apply_global_filters(df)
    if filtered.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    st.caption("💡 Usa los filtros de la barra lateral y el buscador para explorar movimientos específicos.")

    # Buscador de texto
    search_text = st.text_input(
        "🔍 Buscar texto en Concepto o Proveedor",
        help="Busca en los campos 'Concepto' y 'Proveedor' de forma simultánea"
    )

    df_view = filtered.copy()
    if search_text:
        mask = (
            df_view["Concepto"].str.contains(search_text, case=False, na=False)
            | df_view["Proveedor"].str.contains(search_text, case=False, na=False)
        )
        df_view = df_view[mask]

    # Checkboxes para calidad
    st.markdown("#### 🔍 Filtros de calidad de datos")
    col1, col2 = st.columns(2)
    with col1:
        solo_sin_categoria = st.checkbox(
            "Solo sin Categoría",
            help="Muestra únicamente registros que no tienen categoría asignada"
        )
    with col2:
        solo_sin_concepto_r = st.checkbox(
            "Solo sin Concepto Russildi",
            help="Muestra únicamente registros que no tienen Concepto Russildi asignado"
        )

    if solo_sin_categoria:
        df_view = df_view[df_view["Categoría"].isna() | (df_view["Categoría"] == "")]
    if solo_sin_concepto_r:
        df_view = df_view[
            df_view["Concepto Russildi"].isna()
            | (df_view["Concepto Russildi"] == "")
        ]

    # Mostrar contador
    col_count1, col_count2 = st.columns([1, 4])
    with col_count1:
        st.metric("Movimientos encontrados", len(df_view))
    
    if df_view.empty:
        st.warning("No se encontraron movimientos con los filtros seleccionados.")
        return
    
    # Preparar datos para visualización
    df_view_display = df_view[
        [
            "Mes",
            "Fecha",
            "Número",
            "Póliza",
            "Concepto",
            "Proveedor",
            "Monto",
            "Categoría",
            "Concepto Russildi",
        ]
    ].sort_values("Fecha", ascending=False).copy()
    
    # Formatear columna Monto
    df_view_display["Monto"] = df_view_display["Monto"].apply(
        lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00"
    )
    
    # Usar st.data_editor para mejor interactividad (solo lectura)
    st.dataframe(
        df_view_display,
        use_container_width=True,
        height=400,
    )

    # Export
    if not df_view.empty:
        csv = df_view.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "Descargar CSV filtrado",
            data=csv,
            file_name="urbanizacion_filtrado.csv",
            mime="text/csv",
        )


main()