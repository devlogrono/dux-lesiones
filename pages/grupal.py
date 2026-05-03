import streamlit as st
import plotly.express as px
from modules.i18n.i18n import t
import modules.app_config.config as config
import pandas as pd
config.init_config()

from modules.ui.ui_components import data_filters_advanced
from modules.reports.ui_grupal import (
    groupal_metrics,
    grafico_evolucion_dias_baja,
    grafico_evolucion_nuevas_vs_recidivas,
    grafico_evolucion_resumen,
    grafico_tipo_por_severidad,
    grafico_lugar_por_mecanismo,
    grafico_tipo_por_recidiva,
    grafico_impacto_dias_acumulados_por_tipo_y_zona,
    grafico_impacto_scatter_jugadoras,
    grafico_impacto_zona_especifica_detalle,
    grafico_tipo_por_tipo_especifico,
    grafico_tipo_lesion_por_tipo_recidiva
)
from modules.db.db_records import get_records_plus_players_db
from modules.util.util import clean_df

st.header(t("Análisis :red[grupal]"), divider=True)

competicion, posicion, tipo_lesion, rango_rapido, fechas, df_filtrado, records_base_no_fecha = data_filters_advanced()
st.caption(
    t("El delta compara el periodo seleccionado con el periodo anterior equivalente. "
      "El mini gráfico muestra la distribución interna del periodo actual.")
)

st.divider()

# Si la carga de datos falló, detenemos la ejecución del resto del script.
if df_filtrado.empty:
    st.info("No se encontraron registros de lesiones. Por favor, añade datos para continuar.")
    st.stop()

groupal_metrics(
    df_filtrado=df_filtrado,
    records_base=records_base_no_fecha,
    rango_rapido=rango_rapido,
    fechas=fechas,
)

evolucion_tab, distribucion_tab, impacto_tab, jugadoras_tab, tipo_especifico_tab, recidivas_tab, registros_tab = st.tabs(
    [t("Evolución"), t("Distribución"), t("Impacto"), t("Jugadoras"), t("Tipo específico"), t("Recidivas"), t("Registros")]
)

with evolucion_tab:
    fig = grafico_evolucion_resumen(df_filtrado, rango_rapido=rango_rapido, fechas=fechas)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = grafico_evolucion_dias_baja(df_filtrado, rango_rapido=rango_rapido, fechas=fechas)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = grafico_evolucion_nuevas_vs_recidivas(df_filtrado, rango_rapido=rango_rapido, fechas=fechas)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

with distribucion_tab:
    
    fig = grafico_tipo_por_severidad(df_filtrado)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    
    fig = grafico_lugar_por_mecanismo(df_filtrado)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with impacto_tab:
    fig = grafico_impacto_dias_acumulados_por_tipo_y_zona(df_filtrado)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        tipos_disp = [t("TODAS")] + sorted(
            df_filtrado["tipo_lesion"].dropna().astype(str).str.strip().unique().tolist()
        ) if "tipo_lesion" in df_filtrado.columns else [t("TODAS")]

        tipo_sel = st.selectbox(
            t("Tipo de lesión"),
            tipos_disp,
            key="impacto_tipo_detalle"
        )

    with col2:
        zonas_disp = [t("TODAS")] + sorted(
            df_filtrado["zona_cuerpo"].dropna().astype(str).str.strip().unique().tolist()
        ) if "zona_cuerpo" in df_filtrado.columns else [t("TODAS")]

        zona_sel = st.selectbox(
            t("Zona corporal"),
            zonas_disp,
            key="impacto_zona_detalle"
        )

    fig_det = grafico_impacto_zona_especifica_detalle(
        df_filtrado,
        tipo_lesion_sel=tipo_sel,
        zona_cuerpo_sel=zona_sel
    )
    if fig_det:
        st.plotly_chart(fig_det, use_container_width=True)

with jugadoras_tab:
    fig = grafico_impacto_scatter_jugadoras(df_filtrado)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with tipo_especifico_tab:
    fig = grafico_tipo_por_tipo_especifico(df_filtrado)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with recidivas_tab:
    fig = grafico_tipo_por_recidiva(df_filtrado)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    fig = grafico_tipo_lesion_por_tipo_recidiva(df_filtrado)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with registros_tab:
    records = get_records_plus_players_db()
    records_clean = clean_df(records)
    records_filtrados = records_clean[records_clean["id_lesion"].isin(df_filtrado["id_lesion"])].copy()

    if records_filtrados.empty:
        st.info(t("No hay registros para mostrar con los filtros seleccionados."))
    else:
        # -----------------------------
        # Filtros adicionales de tabla
        # -----------------------------
        col_f1, col_f2 = st.columns(2)

        with col_f1:
            estados_disp = [t("TODOS")]
            if "estado_lesion" in records_filtrados.columns:
                estados_disp += sorted(
                    records_filtrados["estado_lesion"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .unique()
                    .tolist()
                )

            estado_sel = st.selectbox(
                t("Filtrar por estado"),
                estados_disp,
                key="tabla_estado_filter"
            )

        with col_f2:
            severidades_disp = [t("TODAS")]
            if "impacto_dias_baja_estimado" in records_filtrados.columns:
                severidades_disp += sorted(
                    records_filtrados["impacto_dias_baja_estimado"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .unique()
                    .tolist()
                )

            severidad_sel = st.selectbox(
                t("Filtrar por severidad"),
                severidades_disp,
                key="tabla_severidad_filter"
            )

        # Aplicar filtros extra
        if estado_sel != t("TODOS") and "estado_lesion" in records_filtrados.columns:
            records_filtrados = records_filtrados[
                records_filtrados["estado_lesion"].fillna("").astype(str).str.strip() == estado_sel
            ].copy()

        if severidad_sel != t("TODAS") and "impacto_dias_baja_estimado" in records_filtrados.columns:
            records_filtrados = records_filtrados[
                records_filtrados["impacto_dias_baja_estimado"].fillna("").astype(str).str.strip() == severidad_sel
            ].copy()

        if records_filtrados.empty:
            st.info(t("No hay registros para mostrar con esos filtros de estado y severidad."))
        else:
            columnas_tabla = [
                c for c in [
                    "nombre_jugadora",
                    "id_lesion",
                    "fecha_lesion",
                    "tipo_lesion",
                    "zona_cuerpo",
                    "zona_especifica",
                    "tipo_especifico",
                    "es_recidiva",
                    "lugar",
                    "mecanismo",
                    "dias_baja_estimado",
                    "impacto_dias_baja_estimado",
                    "estado_lesion",
                    "personal_reporta",
                ]
                if c in records_filtrados.columns
            ]

            df_tabla = records_filtrados[columnas_tabla].copy()

            if "es_recidiva" in df_tabla.columns:
                df_tabla["es_recidiva"] = (
                    df_tabla["es_recidiva"]
                    .fillna(False)
                    .astype(str)
                    .str.strip()
                    .str.lower()
                    .isin(["true", "1", "si", "sí"])
                    .map({True: t("Sí"), False: t("No")})
                )

            if "fecha_lesion" in df_tabla.columns:
                df_tabla["fecha_lesion"] = pd.to_datetime(
                    df_tabla["fecha_lesion"], errors="coerce"
                ).dt.strftime("%Y-%m-%d")

            df_tabla = df_tabla.rename(columns={
                "nombre_jugadora": t("Jugadora"),
                "id_lesion": t("ID lesión"),
                "fecha_lesion": t("Fecha lesión"),
                "tipo_lesion": t("Tipo lesión"),
                "zona_cuerpo": t("Zona corporal"),
                "zona_especifica": t("Zona específica"),
                "tipo_especifico": t("Tipo específico"),
                "es_recidiva": t("Recidiva"),
                "lugar": t("Lugar"),
                "mecanismo": t("Mecanismo"),
                "dias_baja_estimado": t("Días baja"),
                "impacto_dias_baja_estimado": t("Severidad"),
                "estado_lesion": t("Estado"),
                "personal_reporta": t("Reporta"),
            })

            def color_gravedad(val):
                if pd.isna(val):
                    return ""

                v = str(val).strip().upper()

                if v == "MUY GRAVE":
                    return "background-color: rgba(231, 76, 60, 0.28); color: black;"
                if v == "GRAVE":
                    return "background-color: rgba(243, 156, 18, 0.24); color: black;"
                if v in ("MODERADA", "MODERADO"):
                    return "background-color: rgba(255, 193, 7, 0.20); color: black;"
                if v in ("LEVE", "MENOR", "MÍNIMA", "MINIMA"):
                    return "background-color: rgba(46, 204, 113, 0.15); color: black;"
                if v == "SIN BAJA":
                    return "background-color: rgba(111, 168, 220, 0.18); color: black;"
                return ""

            def color_estado(val):
                if pd.isna(val):
                    return ""
                v = str(val).strip().upper()
                if v == "ACTIVO":
                    return "background-color: rgba(255, 140, 0, 0.18);"
                if v == "INACTIVO":
                    return "background-color: rgba(60, 179, 113, 0.18);"
                return ""

            styled_df = df_tabla.style

            if t("Severidad") in df_tabla.columns:
                styled_df = styled_df.map(color_gravedad, subset=[t("Severidad")])

            if t("Estado") in df_tabla.columns:
                styled_df = styled_df.map(color_estado, subset=[t("Estado")])

            event = st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            selected_rows = event.selection.rows if event and event.selection else []

            if selected_rows:
                row_index = selected_rows[0]
                lesion_sel = df_tabla.iloc[row_index]
                jugadora_sel = lesion_sel[t("Jugadora")] if t("Jugadora") in lesion_sel else None

                st.info(f"{t('Registro seleccionado')}: **{lesion_sel.get(t('ID lesión'), '')}**")

                col_btn1, col_btn2 = st.columns([1.4, 6])

                with col_btn1:
                    if st.button(t("Abrir análisis individual"), use_container_width=True, disabled=not jugadora_sel):
                        st.session_state["jugadora_nombre"] = jugadora_sel
                        st.session_state["jugadora_selector_lesiones"] = jugadora_sel
                        st.switch_page("pages/individual.py")