import streamlit as st
import modules.app_config.config as config
config.init_config()

from modules.auth_system.auth_core import init_app_state, validate_login
from modules.auth_system.auth_ui import login_view, menu
from modules.db.db_login import load_all_users_from_db

if st.session_state["auth"]["rol"].lower() != "developer":
    st.switch_page("app.py")

st.header("Area de:red[Desarrollo]", divider=True)

usuarios, simulador, bd = st.tabs(["USUARIOS", "SIMULADOR", "BASE DE DATOS"])
with usuarios:
    st.text("Gestión de usuarios del sistema")
    df = load_all_users_from_db()
    st.dataframe(df)

with simulador:
    st.text("Generar lesiones aleatorias para pruebas")
with bd:
    if st.button(":material/update: Recargar datos"):
        st.cache_data.clear()
        st.rerun()
