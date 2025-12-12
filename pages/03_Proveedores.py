import streamlit as st
import pandas as pd
from utils import ensure_data_loaded, apply_global_filters, format_millions, format_currency

st.set_page_config(layout="wide")

def main():
    ensure_data_loaded()
    df = st.session_state["df"]

    st.title("Proveedores – Concentración del gasto")
    st.caption("Análisis de proveedores y concentración del gasto")

    filtered = apply_global_filters(df)
    if filtered.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    # Asegurar que Monto sea numérico
    filtered_clean = filtered.copy()
    filtered_clean["Monto"] = pd.to_numeric(filtered_clean["Monto"], errors="coerce")
    filtered_clean = filtered_clean.dropna(subset=["Monto", "Proveedor"])
    
    if filtered_clean.empty:
        st.warning("No hay datos válidos con los filtros seleccionados.")
        return

    grp = (
        filtered_clean.groupby("Proveedor")["Monto"]
        .sum()
        .sort_values(ascending=False)
    )
    total = grp.sum()

    top3 = grp.head(3).sum() if len(grp) >= 3 else grp.sum()
    top1_name = grp.index[0]
    top1_monto = grp.iloc[0]
    top1_pct = top1_monto / total * 100 if total != 0 else 0

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Gasto total (periodo filtrado)", format_millions(total))
    with c2:
        st.metric("Proveedores activos", len(grp))
    with c3:
        st.metric(
            "Top 3 concentran",
            f"{top3 / total * 100:,.1f} %" if total != 0 else "0 %",
        )

    st.subheader("📊 Top 10 proveedores por gasto")
    st.caption(f"Mostrando los 10 principales de {len(grp)} proveedores totales")
    st.bar_chart(grp.head(10))

    st.subheader("🔍 Detalle por proveedor")
    proveedor_sel = st.selectbox(
        "Selecciona un proveedor",
        options=grp.index.tolist(),
        index=0,
        help="Selecciona un proveedor para ver el detalle de todas sus transacciones"
    )

    df_prov = filtered_clean[filtered_clean["Proveedor"] == proveedor_sel].copy()
    gasto_prov = df_prov["Monto"].sum()
    num_polizas = df_prov["Monto"].count()
    ticket_prom = df_prov["Monto"].mean()

    c4, c5, c6 = st.columns(3)
    with c4:
        st.metric("Gasto con este proveedor", format_millions(gasto_prov))
    with c5:
        st.metric("Número de pólizas", num_polizas)
    with c6:
        st.metric("Ticket promedio", f"${ticket_prom:,.2f}")

    df_prov_display = df_prov[
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
    df_prov_display["Monto"] = df_prov_display["Monto"].apply(
        lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00"
    )
    
    st.dataframe(df_prov_display, use_container_width=True)


main()