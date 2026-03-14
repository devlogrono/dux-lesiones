import json

import pandas as pd
import streamlit as st
import datetime
from modules.i18n.i18n import t
from modules.util.util import is_valid, to_date


def render_lesion_evolution_form(
    lesion_data,
    tratamientos_list,
    fecha_lesion,
    fecha_observacion_activa_date,
    fecha_observacion_inactiva_date,
    fecha_alta_diagnostico_date,
    alta_medica_value,
    alta_deportiva_value,
    fecha_alta_medica,
    fecha_alta_deportiva,
    disabled_evolution
):
    error = False
    alta_medica = False
    alta_deportiva = False

    st.divider()
    st.subheader(t("Evolución de :red[la lesión]"))

    seguimiento = st.checkbox(
        t("Añadir seguimiento"),
        disabled=disabled_evolution,
        key=f"seguimiento_{st.session_state['form_version']}"
    )

    if seguimiento and not disabled_evolution:
        disabled_evolution = False
    else:
        disabled_evolution = True

    col1, col2, col3 = st.columns([1,2,1])

    with col1:
        fecha_control = st.date_input(
            t("Fecha de control"),
            datetime.date.today(),
            max_value=datetime.date.today(),
            disabled=disabled_evolution,
            key=f"fecha_control_{st.session_state['form_version']}"
        )

    with col2:
        tratamiento_aplicado = st.multiselect(
            t("Tratamiento Aplicado"),
            tratamientos_list,
            placeholder="Selecciona uno o más",
            max_selections=15,
            disabled=disabled_evolution,
            key=f"tratamiento_aplicado_{st.session_state['form_version']}"
        )

    with col3:
        personal_seguimiento = st.text_input(
            t("Personal médico *"),
            disabled=disabled_evolution,
            key=f"personal_seguimiento_{st.session_state['form_version']}"
        )

    incidencias = st.text_area(
        t("Observaciones o incidencias"),
        disabled=disabled_evolution,
        key=f"incidencias_{st.session_state['form_version']}"
    )

    if (fecha_control - fecha_lesion).days < 0:
        error = True
        st.error(t(":material/warning: La fecha de sesión no puede ser anterior a la fecha de registro de la lesion."))

    if not fecha_observacion_activa_date and not fecha_observacion_inactiva_date and not fecha_alta_diagnostico_date:

        st.warning(t(":material/info: La lesión se encuentra pendiente de su evolución, no representa baja deportiva."))
        activar_lesion = st.checkbox(t("Cambiar estado de la lesión"), disabled=disabled_evolution)

        if activar_lesion:

            estado_lesion_value = st.radio(
                t("Seleccionar el nuevo estado:"),
                ["Activa", "Inactiva"],
                horizontal=True,
                index=0
            )

            if estado_lesion_value == "Activa":
                fecha_observacion_activa_date = fecha_control
                incidencias = "Lesión Activada" + " + " + incidencias if incidencias else "Lesión Activada"
                lesion_data["estado_lesion"] = "ACTIVO"
                lesion_data["fecha_observacion_activa"] = fecha_observacion_activa_date.strftime("%Y-%m-%d")
                st.info(t(":material/info: Los días de baja se comenzarán a contar a partir de la fecha actual."))

            else:
                fecha_observacion_inactiva_date = fecha_control
                incidencias = "Lesión Inactivada" + " + " + incidencias if incidencias else "Lesión Inactivada"
                lesion_data["estado_lesion"] = "INACTIVO"
                lesion_data["fecha_observacion_inactiva"] = fecha_observacion_inactiva_date.strftime("%Y-%m-%d")
                st.info(t(":material/info: La lesión quedará inactiva y no podrá ser modificada."))

        alta_medica = False

    else:

        col1, col2, col3 = st.columns([1,1,4])

        with col1:

            alta_medica = st.checkbox(
                t("Alta Médica"),
                value=alta_medica_value,
                disabled=alta_medica_value or disabled_evolution
            )

            if alta_medica:
                if not fecha_alta_medica:
                    fecha_alta_medica = fecha_control

        with col2:

            if alta_medica_value:

                alta_deportiva = st.checkbox(
                    t("Alta Deportiva"),
                    value=alta_deportiva_value,
                    disabled=disabled_evolution
                )

                if alta_deportiva:
                    if not fecha_alta_deportiva:
                        fecha_alta_deportiva = fecha_control
            else:
                alta_deportiva = False

        fecha_alta_deportiva = to_date(fecha_alta_deportiva)
        fecha_alta_medica = to_date(fecha_alta_medica)

        dias_baja_medica_reales = None
        dias_baja_deportiva = None

        if is_valid(fecha_alta_medica):

            if fecha_observacion_activa_date and (fecha_alta_medica - fecha_observacion_activa_date).days < 0:
                error = True
                st.warning(t(":material/warning: La fecha de alta médica no puede ser anterior a la fecha de inicio de la lesión."))

            elif fecha_observacion_activa_date:
                dias_baja_medica_reales = max(0, (fecha_alta_medica - fecha_observacion_activa_date).days)

            else:

                if (fecha_alta_medica - fecha_lesion).days < 0:
                    error = True
                    st.warning(t(":material/warning: La fecha de alta médica no puede ser anterior a la fecha de registro de la lesión."))
                else:
                    dias_baja_medica_reales = max(0, (fecha_alta_medica - fecha_lesion).days)

            incidencias_plus = "Alta Médica" + " + " + incidencias if incidencias else "Alta Médica"
            incidencias = incidencias_plus if not alta_medica_value else incidencias

        if is_valid(fecha_alta_deportiva):

            if (fecha_alta_deportiva - fecha_alta_medica).days < 0:
                error = True
                st.warning(t(":material/warning: La fecha de alta deportiva no puede ser anterior a la fecha de alta médica."))

            else:

                if fecha_observacion_activa_date:
                    dias_baja_deportiva = max(0, (fecha_alta_deportiva - fecha_observacion_activa_date).days)

                else:
                    dias_baja_deportiva = max(0, (fecha_alta_deportiva - fecha_lesion).days)

            incidencias_plus = "Alta Deportiva" + " + " + incidencias if incidencias else "Alta Deportiva"
            incidencias = incidencias_plus

        if dias_baja_medica_reales is not None:
            st.info(f"{t(':material/calendar_clock: Días reales de baja médica:')} {dias_baja_medica_reales} {t('día(s)')}")

        if dias_baja_deportiva is not None:
            st.info(f"{t(':material/calendar_clock: Días reales de baja deportiva:')} {dias_baja_deportiva} {t('día(s)')}")

    show_evolucion_historial(lesion_data)

    if seguimiento and (not personal_seguimiento or not personal_seguimiento.strip()):
        error = True

    tratamiento_aplicado_str = (
        [t.upper() for t in tratamiento_aplicado] if isinstance(tratamiento_aplicado, list) else []
    )

    if not seguimiento:
        return {
            "record_evolucion": {
                "fecha_control": None,
                "tratamiento_aplicado": [],
                "personal_seguimiento": None,
                "observaciones": None,
                "fecha_hora_registro": None,
                "usuario": None
            },
            "alta_medica": False,
            "alta_deportiva": False,
            "fecha_alta_medica": None,
            "fecha_alta_deportiva": None,
            "error": False
        }

    record_evolucion = {
        "fecha_control": fecha_control.strftime("%Y-%m-%d"),
        "tratamiento_aplicado": tratamiento_aplicado_str,
        "personal_seguimiento": personal_seguimiento,
        "observaciones": incidencias,
        "fecha_hora_registro": datetime.datetime.now().isoformat(),
        "usuario": st.session_state['auth']['username']
    }

    return {
        "record_evolucion": record_evolucion,
        "alta_medica": alta_medica,
        "alta_deportiva": alta_deportiva,
        "fecha_alta_medica": fecha_alta_medica,
        "fecha_alta_deportiva": fecha_alta_deportiva,
        "error": error
    }

def show_evolucion_historial(lesion_data: dict):
    """
    Muestra el historial de evolución de una lesión a partir del campo JSON 'evolucion' almacenado en la base de datos.

    Args:
        lesion_data (dict): Diccionario con la información de la lesión. 
                            Debe incluir el campo 'evolucion' (LONGTEXT JSON válido o lista).
    """
    
    evol_raw = lesion_data.get("evolucion")

    # 1. Decodificar según el tipo recibido
    if not evol_raw:
        evolucion_list = []
    elif isinstance(evol_raw, str):
        try:
            evolucion_list = json.loads(evol_raw)
        except json.JSONDecodeError:
            st.warning(t(":material/warning: Error al decodificar el campo 'evolucion'."))
            evolucion_list = []
    elif isinstance(evol_raw, list):
        evolucion_list = evol_raw
    else:
        st.warning(t(":material/warning: Formato desconocido en el campo 'evolucion'."))
        evolucion_list = []

    # 2. Validar que sea una lista con registros
    if not isinstance(evolucion_list, list) or len(evolucion_list) == 0:
        st.divider()
        st.info(t("Sin registros de evolución disponibles."))
        return

    # 3. Convertir a DataFrame
    df_evol = pd.DataFrame(evolucion_list)

    # 4. Convertir fechas
    if "fecha_control" in df_evol.columns:
        df_evol["fecha_control"] = pd.to_datetime(df_evol["fecha_control"], errors="coerce").dt.date  # ✅ solo fecha

    if "fecha_hora_registro" in df_evol.columns:
        df_evol["fecha_hora_registro"] = pd.to_datetime(df_evol["fecha_hora_registro"], errors="coerce")

    # 5. Ordenar por fecha_hora_registro (más reciente primero)
    if "fecha_hora_registro" in df_evol.columns:
        df_evol = df_evol.sort_values("fecha_hora_registro", ascending=False)

    # 6. Formatear tratamiento aplicado
    if "tratamiento_aplicado" in df_evol.columns:
        df_evol["tratamiento_aplicado"] = df_evol["tratamiento_aplicado"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else x
        )

    # 7. Reordenar columnas
    columnas_orden = [
        c for c in [
            "fecha_control", "tratamiento_aplicado", "personal_seguimiento",
            "observaciones", "usuario", "fecha_hora_registro"
        ] if c in df_evol.columns
    ]
    df_evol = df_evol[columnas_orden]

    # 8. Mostrar resultados
    st.divider()
    st.markdown(t("### Historial Evolutivo"))

    num_sesiones = len(df_evol)
    st.caption(f"{t('Total de sesiones registradas:')} **{num_sesiones}**")

    st.dataframe(df_evol, hide_index=True)
