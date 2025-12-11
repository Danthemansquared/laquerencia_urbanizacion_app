import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

MONTH_MAP = {
    # Español completo
    "Enero": 1,
    "Febrero": 2,
    "Marzo": 3,
    "Abril": 4,
    "Mayo": 5,
    "Junio": 6,
    "Julio": 7,
    "Agosto": 8,
    "Septiembre": 9,
    "Setiembre": 9,  # Variante aceptada, pero se mostrará como "Septiembre"
    "Octubre": 10,
    "Noviembre": 11,
    "Diciembre": 12,
    # Abreviaturas en inglés (común en Excel)
    "Jan": 1,  # January
    "Feb": 2,  # February
    "Mar": 3,  # March
    "Apr": 4,  # April
    "May": 5,  # May
    "Jun": 6,  # June
    "Jul": 7,  # July
    "Aug": 8,  # August
    "Sep": 9,  # September
    "Oct": 10,  # October
    "Nov": 11,  # November
    "Dec": 12,  # December
    # Nombres completos en inglés
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

# Mapeo inverso para mostrar nombres de meses (prioriza "Septiembre" sobre "Setiembre")
MONTH_NAMES = {
    1: "Enero",
    2: "Febrero",
    3: "Marzo",
    4: "Abril",
    5: "Mayo",
    6: "Junio",
    7: "Julio",
    8: "Agosto",
    9: "Septiembre",  # Siempre mostrar "Septiembre", no "Setiembre"
    10: "Octubre",
    11: "Noviembre",
    12: "Diciembre",
}

def load_data_from_url(url: str) -> pd.DataFrame:
    """
    Carga datos desde una URL (Google Drive, Google Sheets, Dropbox, etc.)
    
    Args:
        url: URL del archivo Excel o Google Sheets
    
    Returns:
        pd.DataFrame con los datos cargados
    
    Raises:
        Exception: Si no se puede descargar o leer el archivo
    """
    import requests
    import io
    
    # Si es Google Sheets, convertir a formato de exportación Excel
    if "docs.google.com/spreadsheets" in url:
        # Extraer el ID del spreadsheet
        if "/d/" in url:
            sheet_id = url.split("/d/")[1].split("/")[0]
        elif "id=" in url:
            sheet_id = url.split("id=")[1].split("&")[0]
        else:
            raise ValueError("URL de Google Sheets no válida. Debe contener '/d/' o 'id='")
        
        # Convertir a formato de exportación Excel
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    
    # Si es Google Drive, convertir a formato de descarga directa
    elif "drive.google.com" in url:
        # Extraer el ID del archivo
        if "/d/" in url:
            file_id = url.split("/d/")[1].split("/")[0]
        elif "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
        else:
            raise ValueError("URL de Google Drive no válida. Debe contener '/d/' o 'id='")
        
        # Usar formato de descarga directa
        url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    # Descargar el archivo
    try:
        response = requests.get(url, timeout=60, allow_redirects=True)
        response.raise_for_status()
        
        # Verificar que el contenido sea válido
        if len(response.content) == 0:
            raise ValueError("El archivo descargado está vacío")
        
        # Verificar el Content-Type para asegurar que es un archivo Excel
        content_type = response.headers.get('Content-Type', '').lower()
        if 'html' in content_type and len(response.content) < 10000:
            # Podría ser una página de error de Google
            raise ValueError("No se pudo descargar el archivo. Verifica que el archivo esté compartido como 'Cualquiera con el enlace'")
        
        # Leer como Excel especificando el engine explícitamente
        file_like = io.BytesIO(response.content)
        return load_data(file_like)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error al descargar el archivo desde la URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error al procesar el archivo: {str(e)}")


def load_data(file) -> pd.DataFrame:
    """Carga y prepara el archivo de Urbanización."""
    # Si es una URL string, usar load_data_from_url
    if isinstance(file, str) and (file.startswith("http://") or file.startswith("https://")):
        return load_data_from_url(file)
    
    # Si es un objeto file-like o path, leer directamente
    # Especificar engine explícitamente para evitar errores de formato
    try:
        df = pd.read_excel(file, engine='openpyxl')
    except Exception:
        # Si falla con openpyxl, intentar con xlrd para archivos .xls antiguos
        try:
            df = pd.read_excel(file, engine='xlrd')
        except Exception:
            # Último intento sin especificar engine
            df = pd.read_excel(file)

    # Validación mínima de columnas
    expected_cols = {
        "Mes",
        "Número",
        "Fecha",
        "Póliza",
        "Concepto",
        "Proveedor",
        "Monto",
        "Categoría",
        "Concepto Russildi",
    }
    missing = expected_cols.difference(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en el archivo: {missing}")

    # Tipos
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce")

    # Guardar total original para diagnóstico
    rows_total = len(df)
    
    # Normalizar nombres de meses: eliminar espacios, convertir a string
    df["Mes"] = df["Mes"].astype(str).str.strip()
    
    # Crear mapeo más robusto que maneje múltiples variantes
    # Incluir variantes comunes: minúsculas, mayúsculas, capitalizado, etc.
    month_map_extended = {}
    
    # Agregar todas las variantes del MONTH_MAP
    for mes_nombre, mes_num in MONTH_MAP.items():
        # Variantes: original, minúsculas, mayúsculas, capitalizado, título
        variants = [
            mes_nombre.strip(),
            mes_nombre.strip().lower(),
            mes_nombre.strip().upper(),
            mes_nombre.strip().capitalize(),
            mes_nombre.strip().title(),
        ]
        for variant in variants:
            month_map_extended[variant] = mes_num
    
    # Mapear meses usando el diccionario extendido
    df["MesNum"] = df["Mes"].map(month_map_extended)
    
    # Si aún hay valores sin mapear, intentar normalización adicional
    unmapped = df[df["MesNum"].isna()]["Mes"].unique()
    if len(unmapped) > 0:
        # Intentar mapear manualmente casos especiales
        for mes_val in unmapped:
            mes_clean = mes_val.strip().lower()
            # Buscar coincidencias parciales
            for mes_estandar, mes_num in MONTH_MAP.items():
                if mes_clean == mes_estandar.lower().strip():
                    df.loc[df["Mes"] == mes_val, "MesNum"] = mes_num
                    break
    
    # Diagnóstico detallado por mes
    rows_before_clean = len(df)
    
    # Contar registros con problemas
    sin_fecha = df["Fecha"].isna().sum()
    sin_monto = df["Monto"].isna().sum()
    sin_mesnum = df["MesNum"].isna().sum()
    
    # Meses que no se mapearon
    unmapped_months = df[df["MesNum"].isna()]["Mes"].unique()
    unmapped_count = len(df[df["MesNum"].isna()])
    
    # Análisis detallado por mes ANTES de limpiar
    df_diagnostico = df.copy()
    df_diagnostico["tiene_fecha"] = df_diagnostico["Fecha"].notna()
    df_diagnostico["tiene_monto"] = df_diagnostico["Monto"].notna()
    df_diagnostico["tiene_mesnum"] = df_diagnostico["MesNum"].notna()
    
    # Agrupar por mes y contar problemas
    diagnostico_por_mes = df_diagnostico.groupby("Mes").agg({
        "MesNum": "count",  # Total de registros
        "tiene_fecha": "sum",  # Cuántos tienen fecha
        "tiene_monto": "sum",  # Cuántos tienen monto
        "tiene_mesnum": "sum",  # Cuántos tienen mesnum
    }).rename(columns={
        "MesNum": "total",
        "tiene_fecha": "con_fecha",
        "tiene_monto": "con_monto",
        "tiene_mesnum": "con_mesnum"
    })
    
    # Mostrar diagnóstico detallado
    if unmapped_count > 0:
        st.warning(f"⚠️ **{unmapped_count} registros** tienen meses no reconocidos y serán excluidos.")
        st.write(f"**Valores de 'Mes' no reconocidos:** {sorted([m for m in unmapped_months if m != 'nan'])}")
        meses_unicos = sorted([m for m in df['Mes'].unique() if pd.notna(m)])
        st.write(f"**Valores únicos en columna 'Mes' (todos):** {meses_unicos}")
    
    # Crear fechas estimadas para registros sin fecha pero con mes válido
    # Determinar el año más común en los registros que sí tienen fecha
    años_disponibles = df[df["Fecha"].notna()]["Fecha"].dt.year
    año_estimado = int(años_disponibles.mode()[0]) if len(años_disponibles) > 0 else 2025
    
    # Para registros sin fecha pero con MesNum válido, crear fecha estimada (día 15 del mes)
    sin_fecha_con_mes = df[(df["Fecha"].isna()) & (df["MesNum"].notna())]
    if len(sin_fecha_con_mes) > 0:
        for idx in sin_fecha_con_mes.index:
            mes_num = df.loc[idx, "MesNum"]
            # Crear fecha estimada: día 15 del mes correspondiente
            try:
                fecha_estimada = pd.Timestamp(year=año_estimado, month=int(mes_num), day=15)
                df.loc[idx, "Fecha"] = fecha_estimada
            except:
                pass  # Si no se puede crear la fecha, dejar como está
        
        st.info(f"📅 Se crearon fechas estimadas (día 15) para {len(sin_fecha_con_mes)} registros sin fecha pero con mes válido, usando año {año_estimado}.")
    
    # Limpieza: eliminar solo por Monto nulo (ya no por Fecha porque creamos estimadas)
    df_clean = df.dropna(subset=["Monto"])
    rows_after_fecha_monto = len(df_clean)
    
    # Luego eliminar por MesNum nulo
    df_final = df_clean.dropna(subset=["MesNum"])
    rows_final = len(df_final)
    
    # Calcular año después de limpiar
    df_final["Año"] = df_final["Fecha"].dt.year
    
    # Análisis de qué pasó con cada mes
    diagnostico_final = []
    for mes_nombre in sorted(diagnostico_por_mes.index):
        info = diagnostico_por_mes.loc[mes_nombre]
        total_original = int(info["total"])
        con_fecha = int(info["con_fecha"])
        con_monto = int(info["con_monto"])
        con_mesnum = int(info["con_mesnum"])
        
        # Contar cuántos quedaron después de limpiar
        if con_mesnum > 0:
            mes_num = df_diagnostico[df_diagnostico["Mes"] == mes_nombre]["MesNum"].iloc[0]
            registros_finales = len(df_final[df_final["MesNum"] == mes_num])
        else:
            registros_finales = 0
        
        perdidos = total_original - registros_finales
        
        if perdidos > 0:
            diagnostico_final.append({
                "Mes": mes_nombre,
                "Total Original": total_original,
                "Con Fecha": con_fecha,
                "Con Monto": con_monto,
                "Mapeado": "Sí" if con_mesnum > 0 else "No",
                "Registros Finales": registros_finales,
                "Perdidos": perdidos
            })
    
    # Mostrar diagnóstico detallado si hay pérdidas
    if diagnostico_final:
        with st.expander("🔍 Diagnóstico detallado: Registros perdidos por mes", expanded=True):
            df_diag = pd.DataFrame(diagnostico_final)
            st.dataframe(df_diag, use_container_width=True)
            
            # Resumen
            st.write("**Resumen:**")
            for row in diagnostico_final:
                if row["Perdidos"] > 0:
                    razones = []
                    if row["Con Fecha"] < row["Total Original"]:
                        razones.append(f"{row['Total Original'] - row['Con Fecha']} sin fecha")
                    if row["Con Monto"] < row["Total Original"]:
                        razones.append(f"{row['Total Original'] - row['Con Monto']} sin monto")
                    if row["Mapeado"] == "No":
                        razones.append("mes no mapeado")
                    
                    st.write(f"- **{row['Mes']}**: {row['Total Original']} originales → {row['Registros Finales']} finales (perdidos: {row['Perdidos']}) - Razones: {', '.join(razones) if razones else 'desconocidas'}")
    
    # Recontar exclusiones después de crear fechas estimadas
    sin_fecha_final = df_final["Fecha"].isna().sum() if len(df_final) > 0 else 0
    sin_monto_final = (rows_total - rows_final) - unmapped_count - sin_fecha_final
    
    # Mostrar resumen de exclusiones
    excluidos_total = rows_total - rows_final
    if excluidos_total > 0:
        razones = []
        if sin_fecha_final > 0:
            razones.append(f"{sin_fecha_final} por fecha faltante (sin mes válido)")
        if sin_monto_final > 0:
            razones.append(f"{sin_monto_final} por monto faltante")
        if unmapped_count > 0:
            razones.append(f"{unmapped_count} por mes no reconocido")
        
        st.info(
            f"📊 Se cargaron **{rows_final} de {rows_total} registros**. "
            f"**{excluidos_total} registros fueron excluidos:** {'; '.join(razones) if razones else 'por otras razones'}"
        )
    
    return df_final


def ensure_data_loaded():
    """Revisar si ya hay dataframe cargado en session_state."""
    if "df" not in st.session_state:
        st.error(
            "Primero carga el archivo de Urbanización en la página principal (Home)."
        )
        st.stop()


def apply_global_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Dibuja los filtros globales y devuelve el dataframe filtrado."""
    with st.sidebar:
        st.markdown("### Filtros globales")

        # Año
        years = sorted(df["Año"].dropna().unique())
        if len(years) == 0:
            st.warning("No se encontraron años en los datos.")
            return df

        selected_year = st.selectbox("Año", years, index=len(years) - 1)

        df_year = df[df["Año"] == selected_year]

        # Rango de meses
        months_available = sorted(df_year["MesNum"].unique())
        min_month, max_month = min(months_available), max(months_available)

        month_labels = MONTH_NAMES.copy()
        month_start, month_end = st.select_slider(
            "Rango de meses",
            options=months_available,
            value=(min_month, max_month),
            format_func=lambda m: month_labels.get(m, str(m)),
        )

        filtered = df_year[
            (df_year["MesNum"] >= month_start) & (df_year["MesNum"] <= month_end)
        ]

        # Concepto Russildi
        conceptos = sorted(filtered["Concepto Russildi"].dropna().unique())
        selected_conceptos = st.multiselect(
            "Concepto Russildi",
            options=conceptos,
            default=conceptos,
        )
        if selected_conceptos:
            filtered = filtered[filtered["Concepto Russildi"].isin(selected_conceptos)]

        # Categoría
        categorias = sorted(filtered["Categoría"].dropna().unique())
        selected_categorias = st.multiselect(
            "Categoría",
            options=categorias,
            default=categorias,
        )
        if selected_categorias:
            filtered = filtered[filtered["Categoría"].isin(selected_categorias)]

        # Proveedor
        proveedores = sorted(filtered["Proveedor"].dropna().unique())
        selected_proveedores = st.multiselect(
            "Proveedor",
            options=proveedores,
            default=proveedores,
        )
        if selected_proveedores:
            filtered = filtered[filtered["Proveedor"].isin(selected_proveedores)]

        # Umbral de monto
        min_monto = float(filtered["Monto"].min())
        max_monto = float(filtered["Monto"].max())
        if min_monto == max_monto:
            monto_range = (min_monto, max_monto)
        else:
            monto_range = st.slider(
                "Rango de monto por movimiento",
                min_value=float(np.floor(min_monto)),
                max_value=float(np.ceil(max_monto)),
                value=(float(np.floor(min_monto)), float(np.ceil(max_monto))),
                step=1.0,
            )

        filtered = filtered[
            (filtered["Monto"] >= monto_range[0])
            & (filtered["Monto"] <= monto_range[1])
        ]

    return filtered


def format_millions(value: float) -> str:
    """Formatea un valor numérico en millones con formato de moneda."""
    if pd.isna(value) or value == 0:
        return "$0.00 M"
    return f"${value/1_000_000:,.2f} M"


def format_currency(value: float) -> str:
    """Formatea un valor numérico en formato de moneda con $, comas y 2 decimales."""
    if pd.isna(value):
        return "$0.00"
    return f"${value:,.2f}"


def generate_narrative(df: pd.DataFrame, gasto_por_mes: pd.Series, total_ytd: float, 
                       meses_unicos: list, year: int, MONTH_NAMES: dict, 
                       format_millions: callable, prom_ultimos3: float = None, 
                       prom_resto: float = None, delta_pct: float = None) -> str:
    """
    Genera una narrativa automática y dinámica basada en los datos filtrados.
    Se actualiza automáticamente cuando cambian los filtros.
    
    Args:
        df: DataFrame filtrado con los datos
        gasto_por_mes: Serie con gasto por mes
        total_ytd: Total acumulado del periodo
        meses_unicos: Lista de meses únicos en el periodo
        year: Año del periodo
        MONTH_NAMES: Diccionario de nombres de meses
        format_millions: Función para formatear millones
        prom_ultimos3: Promedio de últimos 3 meses (opcional)
        prom_resto: Promedio del resto de meses (opcional)
        delta_pct: Porcentaje de cambio (opcional)
    
    Returns:
        String con la narrativa generada
    """
    # Información básica del periodo
    mes_inicio = MONTH_NAMES.get(meses_unicos[0], str(meses_unicos[0]))
    mes_fin = MONTH_NAMES.get(meses_unicos[-1], str(meses_unicos[-1]))
    meses_count = len(meses_unicos)
    
    # Análisis de gasto por mes
    mes_max = gasto_por_mes.idxmax()
    mes_min = gasto_por_mes.idxmin()
    mes_max_nombre = MONTH_NAMES.get(mes_max, str(mes_max))
    mes_min_nombre = MONTH_NAMES.get(mes_min, str(mes_min))
    gasto_max = gasto_por_mes.loc[mes_max]
    gasto_min = gasto_por_mes.loc[mes_min]
    promedio_mensual = gasto_por_mes.mean()
    run_rate = promedio_mensual * 12
    
    # Calcular variabilidad
    std_gasto = gasto_por_mes.std()
    cv = (std_gasto / promedio_mensual * 100) if promedio_mensual > 0 else 0
    
    # Análisis de tendencia
    if len(gasto_por_mes) >= 2:
        # Calcular tendencia (último mes vs primer mes)
        primer_mes_valor = gasto_por_mes.iloc[0]
        ultimo_mes_valor = gasto_por_mes.iloc[-1]
        tendencia_pct = ((ultimo_mes_valor / primer_mes_valor - 1) * 100) if primer_mes_valor > 0 else 0
        
        # Calcular si hay tendencia creciente o decreciente
        if len(gasto_por_mes) >= 3:
            primeros_3 = gasto_por_mes.head(3).mean()
            ultimos_3 = gasto_por_mes.tail(3).mean()
            tendencia_reciente = ((ultimos_3 / primeros_3 - 1) * 100) if primeros_3 > 0 else 0
        else:
            tendencia_reciente = tendencia_pct
    else:
        tendencia_pct = 0
        tendencia_reciente = 0
    
    # Análisis por conceptos (si está disponible)
    conceptos_info = ""
    if "Concepto Russildi" in df.columns:
        conceptos = df.groupby("Concepto Russildi")["Monto"].sum().sort_values(ascending=False)
        if len(conceptos) > 0:
            top_concepto = conceptos.index[0]
            top_concepto_monto = conceptos.iloc[0]
            top_concepto_pct = (top_concepto_monto / total_ytd * 100) if total_ytd > 0 else 0
            conceptos_info = f" El concepto que más consume recursos es **{top_concepto}** con {format_millions(top_concepto_monto)} ({top_concepto_pct:.1f}% del total)."
    
    # Análisis por proveedores (si está disponible)
    proveedores_info = ""
    if "Proveedor" in df.columns:
        proveedores = df.groupby("Proveedor")["Monto"].sum().sort_values(ascending=False)
        if len(proveedores) > 0:
            num_proveedores = len(proveedores)
            top3_proveedores = proveedores.head(3).sum()
            top3_pct = (top3_proveedores / total_ytd * 100) if total_ytd > 0 else 0
            if top3_pct > 50:
                proveedores_info = f" Se observa una alta concentración de proveedores: los 3 principales concentran el {top3_pct:.1f}% del gasto total."
    
    # Construir narrativa
    narrativa = f"""
### Resumen Ejecutivo

Entre **{mes_inicio}** y **{mes_fin}** de **{year}** se han ejercido **{format_millions(total_ytd)}** en urbanización, 
distribuidos a lo largo de **{meses_count} meses** con un promedio mensual de **{format_millions(promedio_mensual)}**.

### Análisis de Variabilidad

El mes de mayor gasto fue **{mes_max_nombre}** con **{format_millions(gasto_max)}**, mientras que el mes de menor gasto 
fue **{mes_min_nombre}** con **{format_millions(gasto_min)}**. La diferencia entre el mes más caro y el más económico 
es de **{format_millions(gasto_max - gasto_min)}** ({((gasto_max / gasto_min - 1) * 100):.1f}% más alto).
"""
    
    # Agregar análisis de variabilidad
    if cv > 30:
        narrativa += f"\n⚠️ **Alta variabilidad detectada**: El coeficiente de variación es del {cv:.1f}%, indicando una dispersión significativa en los gastos mensuales."
    elif cv < 15:
        narrativa += f"\n✅ **Baja variabilidad**: El coeficiente de variación es del {cv:.1f}%, mostrando gastos relativamente consistentes mes a mes."
    else:
        narrativa += f"\n📊 **Variabilidad moderada**: El coeficiente de variación es del {cv:.1f}%, con fluctuaciones normales en los gastos mensuales."
    
    # Agregar análisis de tendencia
    if len(gasto_por_mes) >= 2:
        narrativa += f"\n\n### Tendencias"
        
        if abs(tendencia_pct) > 10:
            direccion = "creciente" if tendencia_pct > 0 else "decreciente"
            narrativa += f"\nEl gasto muestra una tendencia **{direccion}**: el último mes ({format_millions(ultimo_mes_valor)}) es {abs(tendencia_pct):.1f}% {'mayor' if tendencia_pct > 0 else 'menor'} que el primer mes ({format_millions(primer_mes_valor)})."
        
        if len(gasto_por_mes) >= 3 and abs(tendencia_reciente) > 5:
            direccion_reciente = "aceleración" if tendencia_reciente > 0 else "desaceleración"
            narrativa += f"\nEn los últimos meses se observa una **{direccion_reciente}**: el promedio de los últimos 3 meses es {abs(tendencia_reciente):.1f}% {'mayor' if tendencia_reciente > 0 else 'menor'} que el promedio de los primeros 3 meses."
    
    # Agregar comparación últimos 3 meses
    if prom_ultimos3 is not None and prom_resto is not None and delta_pct is not None and not np.isnan(delta_pct):
        narrativa += f"\n\n### Comparación Reciente"
        if abs(delta_pct) > 10:
            narrativa += f"\nLos últimos 3 meses muestran un gasto promedio de **{format_millions(prom_ultimos3)}**, "
            narrativa += f"lo que representa un {'incremento' if delta_pct > 0 else 'decremento'} del **{abs(delta_pct):.1f}%** "
            narrativa += f"respecto al promedio del resto del periodo ({format_millions(prom_resto)})."
            if delta_pct > 20:
                narrativa += " ⚠️ Este incremento significativo merece atención."
            elif delta_pct < -20:
                narrativa += " ✅ Esta reducción es notable y positiva."
    
    # Agregar proyección
    narrativa += f"\n\n### Proyección"
    narrativa += f"\nCon el ritmo actual de gasto, se estima un **run-rate anual de {format_millions(run_rate)}**."
    
    # Agregar información de conceptos y proveedores
    if conceptos_info:
        narrativa += f"\n\n### Distribución por Conceptos{conceptos_info}"
    if proveedores_info:
        narrativa += f"\n\n### Concentración de Proveedores{proveedores_info}"
    
    # Recomendaciones basadas en datos
    narrativa += f"\n\n### Observaciones Clave"
    
    if gasto_max > promedio_mensual * 1.5:
        narrativa += f"\n- El mes de **{mes_max_nombre}** tuvo un gasto excepcionalmente alto ({format_millions(gasto_max)}), "
        narrativa += f"superando el promedio mensual en {((gasto_max / promedio_mensual - 1) * 100):.1f}%. "
        narrativa += "Se recomienda revisar las causas de este pico."
    
    if meses_count < 6:
        narrativa += f"\n- El periodo analizado abarca solo {meses_count} meses. Para un análisis más robusto, se recomienda incluir más datos históricos."
    
    if promedio_mensual > 0:
        meses_restantes = 12 - meses_count
        if meses_restantes > 0:
            proyeccion_resto = promedio_mensual * meses_restantes
            narrativa += f"\n- Si se mantiene el ritmo actual, se proyecta un gasto adicional de **{format_millions(proyeccion_resto)}** para los {meses_restantes} meses restantes del año."
    
    return narrativa


def format_dataframe_currency(df: pd.DataFrame, currency_columns: list = None) -> pd.DataFrame:
    """
    Formatea columnas de moneda en un DataFrame para visualización.
    
    Args:
        df: DataFrame a formatear
        currency_columns: Lista de nombres de columnas a formatear. Si es None, busca 'Monto'
    
    Returns:
        DataFrame con columnas de moneda formateadas como strings
    """
    df_formatted = df.copy()
    
    if currency_columns is None:
        currency_columns = ['Monto'] if 'Monto' in df.columns else []
    
    for col in currency_columns:
        if col in df_formatted.columns:
            df_formatted[col] = df_formatted[col].apply(
                lambda x: format_currency(x) if pd.notna(x) else "$0.00"
            )
    
    return df_formatted


def prepare_monthly_chart_data(data: pd.Series, include_all_months: bool = False) -> pd.DataFrame:
    """
    Prepara datos mensuales para gráficos asegurando orden cronológico (Enero a Diciembre).
    
    Args:
        data: Serie de pandas con MesNum como índice y valores numéricos
        include_all_months: Si True, incluye todos los meses del 1 al 12 (rellenando con 0)
    
    Returns:
        DataFrame con columnas 'Mes' y 'Valor', ordenado cronológicamente
    """
    # Si include_all_months, crear serie completa del 1 al 12
    if include_all_months:
        all_months = pd.Series(0.0, index=range(1, 13), dtype=float)
        all_months.update(data)
        data = all_months
    
    # Asegurar que esté ordenado por número de mes
    data = data.sort_index()
    
    # Crear orden de meses cronológico (1=Enero, 2=Febrero, ..., 12=Diciembre)
    month_order = [MONTH_NAMES[i] for i in range(1, 13)]
    
    # Crear diccionario con mes_nombre -> valor, solo para meses que tienen datos
    result_dict = {}
    for mes_num in sorted(data.index):
        mes_nombre = MONTH_NAMES.get(mes_num, str(mes_num))
        result_dict[mes_nombre] = data.loc[mes_num]
    
    # Crear lista de datos en orden cronológico estricto
    ordered_data = []
    ordered_meses = []
    for mes_nombre in month_order:
        if mes_nombre in result_dict:
            ordered_meses.append(mes_nombre)
            ordered_data.append(result_dict[mes_nombre])
    
    # Crear DataFrame con columna Mes y Valor
    df_result = pd.DataFrame({
        'Mes': ordered_meses,
        'Valor': ordered_data
    })
    
    return df_result


def create_monthly_bar_chart(data: pd.Series, title: str = "Gasto mensual", 
                             value_column: str = "Gasto", include_all_months: bool = False) -> alt.Chart:
    """
    Crea un gráfico de barras mensual con orden cronológico garantizado usando Altair.
    
    Args:
        data: Serie de pandas con MesNum como índice y valores numéricos
        title: Título del gráfico
        value_column: Nombre de la columna de valores
        include_all_months: Si True, incluye todos los meses del 1 al 12 (rellenando con 0)
    
    Returns:
        Chart de Altair
    """
    df = prepare_monthly_chart_data(data, include_all_months=include_all_months)
    
    # Definir orden de meses para Altair
    month_order = [MONTH_NAMES[i] for i in range(1, 13)]
    
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('Mes:O', 
                title='Mes',
                sort=month_order,  # Orden explícito
                axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Valor:Q', 
                title=value_column,
                axis=alt.Axis(format='$,.0f')),
        tooltip=['Mes', alt.Tooltip('Valor:Q', format='$,.2f')]
    ).properties(
        title=title,
        width=600,
        height=400
    )
    
    return chart


def create_monthly_line_chart(data: pd.Series, title: str = "Gasto acumulado",
                              value_column: str = "Acumulado", include_all_months: bool = False) -> alt.Chart:
    """
    Crea un gráfico de líneas mensual con orden cronológico garantizado usando Altair.
    
    Args:
        data: Serie de pandas con MesNum como índice y valores numéricos
        title: Título del gráfico
        value_column: Nombre de la columna de valores
        include_all_months: Si True, incluye todos los meses del 1 al 12 (rellenando con 0)
    
    Returns:
        Chart de Altair
    """
    df = prepare_monthly_chart_data(data, include_all_months=include_all_months)
    
    # Definir orden de meses para Altair
    month_order = [MONTH_NAMES[i] for i in range(1, 13)]
    
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X('Mes:O',
                title='Mes',
                sort=month_order,  # Orden explícito
                axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('Valor:Q',
                title=value_column,
                axis=alt.Axis(format='$,.0f')),
        tooltip=['Mes', alt.Tooltip('Valor:Q', format='$,.2f')]
    ).properties(
        title=title,
        width=600,
        height=400
    )
    
    return chart