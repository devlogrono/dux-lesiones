import time
import streamlit as st
from modules.i18n.i18n import t
import modules.app_config.config as config
config.init_config()

from modules.ui.records_ui import view_registro_lesion
from modules.db.db_records import save_lesion
from modules.ui.ui_components import selection_header
from modules.util.util import clean_df, sanitize_lesion_data

st.header(t("Seguimiento de :red[lesiones]"), divider="red")

jugadora_seleccionada, posicion, records = selection_header(modo=2)
st.divider()

if not jugadora_seleccionada:
    st.info("Selecciona una jugadora para continuar.")
    st.stop()

if records.empty:    
    st.warning(t("No hay datos de lesiones disponibles."))
    st.stop()   

# if "form_version" not in st.session_state:
#     st.session_state["form_version"] = 0

# if "form_submitted" not in st.session_state:
#     st.session_state.form_submitted = False

if jugadora_seleccionada and isinstance(jugadora_seleccionada, dict):
    nombre_completo = jugadora_seleccionada["nombre_jugadora"]
    id_jugadora = jugadora_seleccionada["id_jugadora"]
    posicion = jugadora_seleccionada["posicion"]

    jugadora_info = {
        "id_jugadora": id_jugadora,
        "nombre_completo": nombre_completo.strip(),
        "posicion": posicion,
        "id_lesion": None
    }

    records = records[records["id_jugadora"] == jugadora_seleccionada["id_jugadora"]]

OPCIONES_ESTATUS = {
    "Todas": t("Todas"),
    "Activas": t("Activas"),
    "En Observación": t("En Observación"),
    "Inactivas": t("Inactivas")
}

estado_filtro_traducido = st.radio(
    t("Filtrar por estatus:"),
    list(OPCIONES_ESTATUS.values()),
    horizontal=True,
    index=list(OPCIONES_ESTATUS.keys()).index("Todas")
)

# 🔥 Mapeo invertido: valor traducido → clave original
estado_filtro = next(
    (k for k, v in OPCIONES_ESTATUS.items() if v == estado_filtro_traducido),
    "Todas"
)

if estado_filtro == "Activas":
    records = records[records["estado_lesion"].str.lower() == "activo"]
elif estado_filtro == "En Observación":
    records = records[records["estado_lesion"].str.lower() == "observacion"]
elif estado_filtro == "Inactivas":
    records = records[records["estado_lesion"].str.lower() == "inactivo"]

# --- Mensaje dinámico según cantidad ---
num_lesiones = len(records)
if num_lesiones == 0:
    st.info(f"{t('No se encontraron lesiones')} {estado_filtro.lower()}")
    st.stop()
elif num_lesiones == 1:
    st.markdown(f"**{t('Se encontró 1 lesión')} {estado_filtro.lower()[:-1] if estado_filtro != 'Todas' else ''} {t('registrada')}**")
else:
    st.markdown(f"**{t('Se encontraron')} {num_lesiones} {t('lesiones')} {estado_filtro.lower()[:] if estado_filtro != 'Todas' else ''} {t('registradas')}**")

selection_context = {
    "id_jugadora": jugadora_info["id_jugadora"],
    "estado_filtro": estado_filtro
}

previous_context = st.session_state.get("lesion_selection_context")

# limpiar selección si cambia jugadora o filtro
if previous_context != selection_context:
    st.session_state.pop("selected_lesion_id", None)
    st.session_state.pop("tabla_lesiones", None)

st.session_state["lesion_selection_context"] = selection_context

# === Mostrar resultado ===
df_filtrado = clean_df(records)

#st.dataframe(df_filtrado)
event = st.dataframe(
        df_filtrado[["id_lesion", "nombre_jugadora", "fecha_lesion", "zona_cuerpo", "zona_especifica", 
                     "tipo_lesion", "personal_reporta", "estado_lesion"]],
        on_select="rerun",
        selection_mode="single-row",
        key="tabla_lesiones"
    )

selected_rows = event.selection.rows if event.selection else []

previous_selected = st.session_state.get("selected_lesion_id")

if selected_rows:
    row_index = selected_rows[0]
    selected_id = df_filtrado.iloc[row_index]["id_lesion"]
    st.session_state["selected_lesion_id"] = selected_id

elif previous_selected and event.selection is not None:
    # el usuario quitó la selección manualmente
    st.session_state.pop("selected_lesion_id", None)

id_buscar = st.session_state.get("selected_lesion_id")

if not id_buscar:
    st.stop()

# -----------------------------------------
# si NO hay selección → limpiar
# -----------------------------------------
# else:
#     if "selected_lesion_id" in st.session_state:
#         st.session_state.pop("selected_lesion_id", None)

if "selected_lesion_id" not in st.session_state:
    st.stop()

# ------------------------------------
# cargar lesión
# ------------------------------------
if id_buscar:

    lesion = records.loc[records["id_lesion"] == id_buscar]
    if not lesion.empty:

        lesion_data = lesion.iloc[0].to_dict()
        lesion_data = sanitize_lesion_data(lesion_data)

        estado_original = lesion_data.get("estado_lesion")

        st.divider()
        st.info(f"Editando lesión: {id_buscar}")
        record, error, disabled_evolution, form_changed, evolucion_changed, disabled_edit = view_registro_lesion(
            modo="editar", jugadora_info=jugadora_info, lesion_data=lesion_data)

    else:
        st.error(t("No se encontró ninguna lesión con ese ID."))
        st.stop()


    ######################## GUARDADO Y REINICIO ########################
    #st.session_state.form_submitted = False
    # Inicializar control de estado del botón
    if "form_submitted" not in st.session_state:
        st.session_state.form_submitted = False

    # ----------------------------------
    # Control del botón Guardar
    # ----------------------------------

    disabled_guardar = True

    if estado_original == "INACTIVO":
        disabled_guardar = True
    elif evolucion_changed:
        disabled_guardar = False
    elif not disabled_edit and form_changed:
        disabled_guardar = False

    if error:
        disabled_guardar = True

    submitted = st.button(t("Guardar"),disabled=disabled_guardar, type="primary")
    success = False

    if submitted:
        # Evitar dobles clics
        st.session_state.form_submitted = True

        try:
            with st.spinner(t("Actualizando lesión...")):
                # sincronizar estado real de la lesión
                if evolucion_changed:

                    ultima_evolucion = record["evolucion"][-1]

                    if "Lesión Inactivada" in ultima_evolucion.get("observaciones", ""):
                        record["estado_lesion"] = "INACTIVO"

                    elif "Lesión Activada" in ultima_evolucion.get("observaciones", ""):
                        record["estado_lesion"] = "ACTIVO"
                success = save_lesion(record, "editar")

                if success:
                    # Si el guardado fue exitoso
                    st.session_state["flash"] = t(":material/done_all: Lesión guardada correctamente.")
                else:
                    # Si hubo error en save_lesion, desbloquear botón
                    st.warning(t(":material/warning: No se pudo guardar la lesión. Revisa los datos e inténtalo nuevamente."))
                    st.session_state.form_submitted = False

        except Exception as e:
            # Captura cualquier error inesperado
            st.error(f"{t(':material/warning: Error inesperado al guardar la lesión:')} {e}")
            st.session_state.form_submitted = False

    # --- Mostrar mensaje flash tras guardar ---
    if st.session_state.get("flash"):
        st.success(st.session_state["flash"])
        st.session_state["flash"] = None
        st.session_state.form_submitted = False

    lesion_inactivada = (
        estado_original != "INACTIVO"
        and record.get("estado_lesion") == "INACTIVO"
    )

    if success:

        if lesion_inactivada:
            st.session_state["flash"] = t(":material/done_all: Lesión inactivada correctamente.")
            st.session_state["form_version"] += 1
            #st.session_state["from_save"] = True
            st.rerun()

        elif evolucion_changed:
            st.session_state["flash"] = t(":material/done_all: Seguimiento guardado correctamente.")
            st.session_state["form_version"] += 1
            #st.session_state["from_save"] = True
            

            # keys_to_clear = [
            #     f"fecha_control_{st.session_state['form_version']}",
            #     f"tratamiento_aplicado_{st.session_state['form_version']}",
            #     f"personal_seguimiento_{st.session_state['form_version']}",
            #     f"incidencias_{st.session_state['form_version']}"
            # ]

            # for k in keys_to_clear:
            #     if k in st.session_state:
            #         del st.session_state[k]
            
            st.rerun()

        else:
            st.session_state["flash"] = t(":material/done_all: Lesión actualizada correctamente.")
            st.session_state["form_version"] += 1
            st.rerun()