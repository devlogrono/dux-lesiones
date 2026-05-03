import streamlit as st
from modules.i18n.i18n import t

import modules.app_config.config as config
config.init_config()

from modules.util.util import clean_df
from modules.ui.ui_components import main_metrics,latest_lesiones_panel
from modules.db.db_records import get_records_plus_players_db

st.header(t("Resumen de :red[Lesiones] (1er Equipo)"), divider=True)

records = get_records_plus_players_db(plantel="1FF")
resumen = main_metrics(records)

st.subheader(t("Ultimas :red[lesiones]"))
df_filtrado = clean_df(resumen)
latest_lesiones_panel(df_filtrado)