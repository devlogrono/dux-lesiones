import streamlit as st
from modules.i18n.i18n import t
import modules.app_config.config as config
config.init_config()

from modules.ui.lesion_ui import view_registro_lesion_read
from modules.util.util import clean_df, sanitize_lesion_data
from modules.ui.ui_components import selection_header, main_metrics
from modules.reports.ui_individual import (grafico_zonas_lesionadas, grafico_tipo_mecanismo, grafico_evolucion_lesiones, 
                      grafico_tratamientos, grafico_dias_baja, grafico_recidivas, player_block_dux)

st.header(t("Análisis :red[individual]"), divider=True)

jugadora_seleccionada, posicion, records = selection_header(modo=2)

st.divider()

#st.dataframe(jugadora_seleccionada)
player_block_dux(jugadora_seleccionada)
resumen = main_metrics(records, modo="reporte")

#st.dataframe(records)

@st.dialog(t(":red[Visualizador] de lesiones"), width="large")
def dialog_lesion(lesion_data):
    with st.container(border=True):
        view_registro_lesion_read(
            jugadora_info=jugadora_seleccionada,
            lesion_data=lesion_data
        )

tab1, tab2 = st.tabs([t("Graficos"), t("Registros")])

with tab1:
    col1, col2 = st.columns([1,1])
    with col1:
        fig = grafico_evolucion_lesiones(records)
        if fig: st.plotly_chart(fig)

        fig = grafico_tipo_mecanismo(records)
        if fig: st.plotly_chart(fig)

        fig = grafico_dias_baja(records)
        if fig: st.plotly_chart(fig)

    with col2:
        fig = grafico_zonas_lesionadas(records)
        if fig: st.plotly_chart(fig)

        fig = grafico_tratamientos(records)
        if fig: st.plotly_chart(fig)

        fig = grafico_recidivas(records)
        if fig: st.plotly_chart(fig)

with tab2:
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