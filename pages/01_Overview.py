import streamlit as st
import pandas as pd
import numpy as np
from utils import ensure_data_loaded, apply_global_filters, format_millions, format_currency, MONTH_NAMES, create_monthly_bar_chart, create_monthly_line_chart, generate_narrative

st.set_page_config(layout="wide")

def main():
    ensure_data_loaded()
    df = st.session_state["df"]

    st.title("Overview – Ritmo y control del gasto")
    st.caption("Vista general del gasto con análisis de tendencias y narrativa automática")

    filtered = apply_global_filters(df)

    if filtered.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    # KPIs
    # Asegurar que Monto sea numérico y eliminar valores nulos
    filtered_clean = filtered.copy()
    filtered_clean["Monto"] = pd.to_numeric(filtered_clean["Monto"], errors="coerce")
    filtered_clean = filtered_clean.dropna(subset=["Monto"])
    
    if filtered_clean.empty:
        st.warning("No hay datos válidos con los filtros seleccionados.")
        return
    
    total_ytd = filtered_clean["Monto"].sum()
    meses_unicos = sorted(filtered_clean["MesNum"].dropna().unique())
    meses_count = len(meses_unicos)

    gasto_por_mes = filtered_clean.groupby("MesNum")["Monto"].sum().sort_index()
    promedio_mensual = gasto_por_mes.mean() if len(gasto_por_mes) > 0 else 0
    run_rate = promedio_mensual * 12

    mes_max = gasto_por_mes.idxmax()
    mes_min = gasto_por_mes.idxmin()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Gasto acumulado periodo filtrado", format_millions(total_ytd))
    with c2:
        st.metric("Meses con datos", meses_count)
    with c3:
        st.metric("Run-rate anual estimado", format_millions(run_rate))
    with c4:
        mes_max_nombre = MONTH_NAMES.get(mes_max, str(mes_max))
        st.metric(
            "Mes más caro",
            f"{mes_max_nombre} ({format_millions(gasto_por_mes.loc[mes_max])})",
        )

    # Gráficos
    st.subheader("Gasto mensual")

    col1, col2 = st.columns(2)

    with col1:
        # Gráfico de barras con Altair (orden cronológico garantizado)
        chart_barras = create_monthly_bar_chart(
            gasto_por_mes, 
            title="Gasto mensual",
            value_column="Gasto (MXN)",
            include_all_months=False
        )
        st.altair_chart(chart_barras, use_container_width=True)

    with col2:
        # Acumulado - Gráfico de líneas con Altair
        gasto_acum = gasto_por_mes.cumsum()
        chart_lineas = create_monthly_line_chart(
            gasto_acum,
            title="Gasto acumulado",
            value_column="Acumulado (MXN)",
            include_all_months=False
        )
        st.altair_chart(chart_lineas, use_container_width=True)

    # Comparación últimos 3 meses vs resto
    if meses_count >= 4:
        ultimos3 = meses_unicos[-3:]
        resto = [m for m in meses_unicos if m not in ultimos3]

        prom_ultimos3 = gasto_por_mes.loc[ultimos3].mean()
        prom_resto = gasto_por_mes.loc[resto].mean()

        delta_pct = (prom_ultimos3 / prom_resto - 1) * 100 if prom_resto != 0 else np.nan

        st.subheader("Comparación últimos 3 meses vs resto del año")
        c5, c6, c7 = st.columns(3)
        with c5:
            st.metric(
                "Promedio resto meses",
                format_millions(prom_resto),
            )
        with c6:
            st.metric(
                "Promedio últimos 3 meses",
                format_millions(prom_ultimos3),
                delta=f"{delta_pct:,.1f} %" if not np.isnan(delta_pct) else "NA",
            )
        with c7:
            st.write("Meses últimos 3:", ", ".join(MONTH_NAMES.get(m, str(m)) for m in ultimos3))

    # Narrativa automática e inteligente
    st.subheader("Narrativa automática")
    
    # Calcular promedios para la narrativa si están disponibles
    prom_ultimos3_val = None
    prom_resto_val = None
    delta_pct_val = None
    
    if meses_count >= 4:
        ultimos3 = meses_unicos[-3:]
        resto = [m for m in meses_unicos if m not in ultimos3]
        prom_ultimos3_val = gasto_por_mes.loc[ultimos3].mean()
        prom_resto_val = gasto_por_mes.loc[resto].mean()
        delta_pct_val = (prom_ultimos3_val / prom_resto_val - 1) * 100 if prom_resto_val != 0 else np.nan
    
    year = int(filtered["Año"].iloc[0]) if not filtered.empty else 2025
    
    # Generar narrativa dinámica
    narrativa = generate_narrative(
        df=filtered_clean,
        gasto_por_mes=gasto_por_mes,
        total_ytd=total_ytd,
        meses_unicos=meses_unicos,
        year=year,
        MONTH_NAMES=MONTH_NAMES,
        format_millions=format_millions,
        prom_ultimos3=prom_ultimos3_val,
        prom_resto=prom_resto_val,
        delta_pct=delta_pct_val
    )
    
    st.markdown(narrativa)


main()