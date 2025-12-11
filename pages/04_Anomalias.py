import streamlit as st
import pandas as pd
import numpy as np
from utils import ensure_data_loaded, apply_global_filters, MONTH_NAMES, format_millions, create_monthly_bar_chart

st.set_page_config(layout="wide")

def main():
    ensure_data_loaded()
    df = st.session_state["df"]

    st.title("Anomalías – Meses y pólizas atípicas")

    filtered = apply_global_filters(df)
    if filtered.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    # Asegurar que Monto sea numérico
    filtered_clean = filtered.copy()
    filtered_clean["Monto"] = pd.to_numeric(filtered_clean["Monto"], errors="coerce")
    filtered_clean = filtered_clean.dropna(subset=["Monto"])
    
    if filtered_clean.empty:
        st.warning("No hay datos válidos con los filtros seleccionados.")
        return


    # 1) Meses pico
    st.subheader("Meses pico (nivel agregado)")
    gasto_mes = filtered_clean.groupby("MesNum")["Monto"].sum().sort_index()
    prom = gasto_mes.mean()
    std = gasto_mes.std(ddof=0)

    upper = prom + 1.5 * std
    lower = prom - 1.5 * std

    meses_out_alta = gasto_mes[gasto_mes > upper]
    meses_out_baja = gasto_mes[gasto_mes < lower]

    col1, col2 = st.columns(2)
    with col1:
        st.write("Promedio mensual:", format_millions(prom))
        st.write("Límite alto:", format_millions(upper))
        st.write("Límite bajo:", format_millions(lower))
    with col2:
        # Gráfico de barras con Altair (orden cronológico garantizado)
        chart_barras = create_monthly_bar_chart(
            gasto_mes,
            title="Gasto por mes",
            value_column="Gasto (MXN)",
            include_all_months=False
        )
        st.altair_chart(chart_barras, use_container_width=True)

    if not meses_out_alta.empty:
        st.markdown("**Meses con gasto inusualmente alto:**")
        for m, v in meses_out_alta.items():
            st.write(f"- {MONTH_NAMES.get(m, str(m))}: {format_millions(v)}")
    else:
        st.markdown("No se detectaron meses inusualmente altos.")

    if not meses_out_baja.empty:
        st.markdown("**Meses con gasto inusualmente bajo:**")
        for m, v in meses_out_baja.items():
            st.write(f"- {MONTH_NAMES.get(m, str(m))}: {format_millions(v)}")
    else:
        st.markdown("No se detectaron meses inusualmente bajos.")

    # 2) Pólizas outlier por concepto (simple: > 3x mediana)
    st.subheader("Pólizas atípicas por concepto (Monto > 3× mediana del concepto)")

    outlier_rows = []
    for concepto, df_con in filtered_clean.groupby("Concepto Russildi"):
        med = df_con["Monto"].median()
        if med <= 0:
            continue
        mask = df_con["Monto"] > 3 * med
        df_out = df_con[mask].copy()
        if df_out.empty:
            continue
        df_out["MedianaConcepto"] = med
        df_out["VecesMediana"] = df_out["Monto"] / med
        outlier_rows.append(df_out)

    if outlier_rows:
        df_outliers = pd.concat(outlier_rows, ignore_index=True)

        df_outliers_display = df_outliers[
            [
                "Mes",
                "Fecha",
                "Póliza",
                "Concepto",
                "Proveedor",
                "Monto",
                "Concepto Russildi",
                "MedianaConcepto",
                "VecesMediana",
            ]
        ].sort_values("VecesMediana", ascending=False).copy()
        
        # Formatear columnas de moneda
        df_outliers_display["Monto"] = df_outliers_display["Monto"].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00"
        )
        df_outliers_display["MedianaConcepto"] = df_outliers_display["MedianaConcepto"].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) else "$0.00"
        )
        
        st.dataframe(df_outliers_display, use_container_width=True)
    else:
        st.info("No se encontraron pólizas que superen 3× la mediana de su concepto.")


main()