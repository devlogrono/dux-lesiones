import streamlit as st
from modules.i18n.i18n import t
import modules.app_config.config as config
config.init_config()

from modules.ui.lesion_ui import view_registro_lesion_read
from modules.util.util import clean_df, sanitize_lesion_data
from modules.ui.ui_components import selection_header, main_metrics
from modules.reports.ui_grupal import (
    grafico_tipo_por_severidad,
    grafico_lugar_por_mecanismo,
    grafico_tipo_por_tipo_especifico,
    grafico_tipo_lesion_por_tipo_recidiva,
    grafico_impacto_dias_acumulados_por_tipo_y_zona,
    grafico_impacto_zona_especifica_detalle
)
from modules.reports.ui_individual import (grafico_zonas_lesionadas, grafico_tipo_mecanismo, grafico_evolucion_lesiones, 
                     grafico_dias_baja, grafico_recidivas, player_block_dux, render_active_injury_progress, grafico_tipo_zona_tratamiento, grafico_tipo_recidiva)

st.header(t("Análisis :red[individual]"), divider=True)

jugadora_seleccionada, posicion, records = selection_header(modo=2)

st.divider()

player_block_dux(jugadora_seleccionada)
resumen = main_metrics(records, modo="reporte")
render_active_injury_progress(resumen)

@st.dialog(t(":red[Visualizador] de lesiones"), width="large")
def dialog_lesion(lesion_data):
    with st.container(border=True):
        view_registro_lesion_read(
            jugadora_info=jugadora_seleccionada,
            lesion_data=lesion_data
        )

tab_historial, tab_distribucion, tab_impacto, tab_tratamientos, tab_tipo_especifico, tab_recidivas, tab_registros = st.tabs(
    [t("Historial"), t("Distribución"), t("Impacto"), t("Tratamientos"), t("Tipo específico"), t("Recidivas"), t("Registros")]
)

with tab_historial:
    fig = grafico_evolucion_lesiones(records)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with tab_distribucion:
    fig = grafico_tipo_por_severidad(records)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    fig = grafico_lugar_por_mecanismo(records)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with tab_impacto:
    fig = grafico_impacto_dias_acumulados_por_tipo_y_zona(records)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        tipos_disp = [t("TODAS")] + sorted(
            records["tipo_lesion"].dropna().astype(str).str.strip().unique().tolist()
        ) if "tipo_lesion" in records.columns else [t("TODAS")]

        tipo_sel = st.selectbox(
            t("Tipo de lesión"),
            tipos_disp,
            key="individual_impacto_tipo_detalle"
        )

    with col2:
        zonas_disp = [t("TODAS")] + sorted(
            records["zona_cuerpo"].dropna().astype(str).str.strip().unique().tolist()
        ) if "zona_cuerpo" in records.columns else [t("TODAS")]

        zona_sel = st.selectbox(
            t("Zona corporal"),
            zonas_disp,
            key="individual_impacto_zona_detalle"
        )

    fig_det = grafico_impacto_zona_especifica_detalle(
        records,
        tipo_lesion_sel=tipo_sel,
        zona_cuerpo_sel=zona_sel
    )
    if fig_det:
        st.plotly_chart(fig_det, use_container_width=True)

with tab_tipo_especifico:
    fig = grafico_tipo_por_tipo_especifico(records)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        
    fig = grafico_tipo_mecanismo(records)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with tab_tratamientos:
    fig = grafico_tipo_zona_tratamiento(records)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with tab_recidivas:
    fig = grafico_tipo_recidiva(records)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

    fig = grafico_tipo_lesion_por_tipo_recidiva(records)
    if fig:
        st.plotly_chart(fig, use_container_width=True)

with tab_registros:
    # aquí dejas tu tabla de registros / visualizador
    records_clean = clean_df(records)

    event = st.dataframe(
        records_clean,
        on_select="rerun",
        selection_mode="single-row"
    )

    selected_rows = event.selection.rows

    # ------------------------------------
    # Selección de registro
    # ------------------------------------
    if selected_rows:

        row_index = selected_rows[0]
        id_buscar = records_clean.iloc[row_index]["id_lesion"]

        lesion = records.loc[records["id_lesion"] == id_buscar]

        if not lesion.empty:

            lesion_data = lesion.iloc[0].to_dict()
            lesion_data = sanitize_lesion_data(lesion_data)

            dialog_lesion(lesion_data)

        else:
            st.error(t("No se encontró ninguna lesión con ese ID."))