import streamlit as st
import pandas as pd
from utils import ensure_data_loaded, apply_global_filters, format_millions, format_dataframe_currency

st.set_page_config(layout="wide")

def main():
    ensure_data_loaded()
    df = st.session_state["df"]

    st.title("Conceptos – ¿En qué se está yendo el dinero?")

    filtered = apply_global_filters(df)
    if filtered.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    # Asegurar que Monto sea numérico
    filtered_clean = filtered.copy()
    filtered_clean["Monto"] = pd.to_numeric(filtered_clean["Monto"], errors="coerce")
    filtered_clean = filtered_clean.dropna(subset=["Monto", "Concepto Russildi"])
    
    if filtered_clean.empty:
        st.warning("No hay datos válidos con los filtros seleccionados.")
        return
    
    # Agregado por Concepto Russildi
    grp = (
        filtered_clean.groupby("Concepto Russildi")["Monto"]
        .sum()
        .sort_values(ascending=False)
    )

    total = grp.sum()
    top3 = grp.head(3).sum() if len(grp) >= 3 else grp.sum()
    top_concepto = grp.index[0]
    top_concepto_monto = grp.iloc[0]
    top_concepto_pct = top_concepto_monto / total * 100 if total != 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Gasto total (periodo filtrado)", format_millions(total))
    with c2:
        st.metric("Conceptos activos", len(grp))
    with c3:
        st.metric(
            "Top 3 concentran",
            f"{top3 / total * 100:,.1f} %" if total != 0 else "0 %",
        )

    st.subheader("Top conceptos por gasto")
    st.bar_chart(grp)

    # Tabla resumen
    st.subheader("Detalle por concepto")

    # Agregar usando diccionario (sintaxis más compatible)
    df_concept = filtered_clean.groupby("Concepto Russildi").agg({
        "Monto": ["sum", "count", "mean"]
    })
    
    # Aplanar MultiIndex de columnas
    df_concept.columns = ["Gasto_Total", "Num_Polizas", "Ticket_Promedio"]
    df_concept = df_concept.reset_index()
    df_concept = df_concept.set_index("Concepto Russildi")
    df_concept = df_concept.sort_values("Gasto_Total", ascending=False)
    
    # Calcular porcentaje después de la agregación
    df_concept["Porcentaje"] = (df_concept["Gasto_Total"] / total * 100) if total != 0 else 0
    
    # Formatear columnas de moneda
    df_concept_display = df_concept.copy()
    df_concept_display["Gasto_Total"] = df_concept_display["Gasto_Total"].apply(
        lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00"
    )
    df_concept_display["Ticket_Promedio"] = df_concept_display["Ticket_Promedio"].apply(
        lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00"
    )
    df_concept_display["Porcentaje"] = df_concept_display["Porcentaje"].apply(
        lambda x: f"{x:,.2f}%" if pd.notna(x) else "0.00%"
    )

    st.dataframe(df_concept_display, use_container_width=True)

    # Drill-down: seleccionar un concepto
    st.subheader("Movimientos de un concepto específico")
    concepto_sel = st.selectbox(
        "Selecciona un Concepto Russildi",
        options=df_concept.index.tolist(),
    )

    df_detalle = filtered_clean[filtered_clean["Concepto Russildi"] == concepto_sel].copy()
    st.markdown(
        f"**{concepto_sel}** – {len(df_detalle)} movimientos, "
        f"por un total de {format_millions(df_detalle['Monto'].sum())}"
    )
    df_detalle_display = df_detalle[
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
    ].sort_values("Monto", ascending=False).copy()
    
    # Formatear columna Monto
    df_detalle_display["Monto"] = df_detalle_display["Monto"].apply(
        lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00"
    )
    
    st.dataframe(df_detalle_display, use_container_width=True)


main()