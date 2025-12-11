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

    st.markdown("Usa los filtros de la barra lateral y el buscador para explorar movimientos específicos.")

    # Buscador de texto
    search_text = st.text_input("Buscar texto en Concepto o Proveedor")

    df_view = filtered.copy()
    if search_text:
        mask = (
            df_view["Concepto"].str.contains(search_text, case=False, na=False)
            | df_view["Proveedor"].str.contains(search_text, case=False, na=False)
        )
        df_view = df_view[mask]

    # Checkboxes para calidad
    col1, col2, col3 = st.columns(3)
    with col1:
        solo_sin_categoria = st.checkbox("Solo sin Categoría")
    with col2:
        solo_sin_concepto_r = st.checkbox("Solo sin Concepto Russildi")
    with col3:
        st.write("")  # placeholder

    if solo_sin_categoria:
        df_view = df_view[df_view["Categoría"].isna() | (df_view["Categoría"] == "")]
    if solo_sin_concepto_r:
        df_view = df_view[
            df_view["Concepto Russildi"].isna()
            | (df_view["Concepto Russildi"] == "")
        ]

    st.write(f"Movimientos encontrados: {len(df_view)}")

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
    
    st.dataframe(df_view_display, use_container_width=True)

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