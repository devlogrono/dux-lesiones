import streamlit as st
from modules.i18n.i18n import t
import modules.app_config.config as config
from modules.util.util import clean_df
from modules.ui.ui_components import selection_header
from modules.db.db_records import delete_lesiones

config.init_config()

# -----------------------------------------
# Seguridad de acceso
# -----------------------------------------
if st.session_state["auth"]["rol"].lower() not in ["admin", "developer"]:
    st.switch_page("app.py")

st.header(t("Administrador de :red[registros]"), divider=True)

jugadora_seleccionada, posicion, records = selection_header(modo=3)

if records.empty:
    st.info("No se encontraron registros de lesiones. Por favor, añade datos para continuar.")
    st.stop()

records = clean_df(records)

# -----------------------------------------
# Tabla interactiva con selección
# -----------------------------------------
event = st.dataframe(
    records,
    on_select="rerun",
    selection_mode="multi-row"
)

selected_rows = event.selection.rows

# Obtener IDs seleccionados
ids_seleccionados = []

if selected_rows:
    ids_seleccionados = records.iloc[selected_rows]["id_lesion"].tolist()

# Debug developer
if st.session_state["auth"]["rol"].lower() == "developer":
    st.write(t("Registros seleccionados:"), ids_seleccionados)

# -----------------------------------------
# Descarga CSV
# -----------------------------------------
csv_data = records.to_csv(index=False).encode("utf-8")

exito, mensaje = False, ""

# -----------------------------------------
# Diálogo confirmación
# -----------------------------------------
@st.dialog(t("Confirmar"), width="small")
def dialog_eliminar():

    st.warning(f"¿{t('Está seguro de eliminar')} {len(ids_seleccionados)} {t('elemento')}(s)?")

    _, col2, col3 = st.columns([1.8, 1, 1])

    with col2:
        if st.button(t(":material/cancel: Cancelar")):
            st.rerun()

    with col3:
        if st.button(t(":material/delete: Eliminar"), type="primary"):

            exito, mensaje = delete_lesiones(ids_seleccionados)

            if exito:
                st.session_state["reload_flag"] = True
            else:
                st.error(mensaje)

            st.rerun()

# -----------------------------------------
# Mensaje éxito
# -----------------------------------------
if st.session_state.get("reload_flag") and exito:
    st.success(mensaje)
    st.session_state["reload_flag"] = False

# -----------------------------------------
# Botones
# -----------------------------------------
col1, col2, col3, _ = st.columns([2,2,2,2])

with col1:
    if st.button(
        t(":material/delete: Eliminar seleccionados"),
        disabled=len(ids_seleccionados) == 0
    ):
        dialog_eliminar()

with col2:
    st.download_button(
        label=t(":material/download: Descargar registros en CSV"),
        data=csv_data,
        file_name="registros_wellness.csv",
        mime="text/csv"
    )

# JSON developer
if st.session_state["auth"]["rol"].lower() == "developer":
    with col3:
        json_data = records.to_json(
            orient="records",
            force_ascii=False,
            indent=2
        )

        st.download_button(
            label=t(":material/download: Descargar registros en JSON"),
            data=json_data.encode("utf-8"),
            file_name="registros_wellness.json",
            mime="application/json"
        )