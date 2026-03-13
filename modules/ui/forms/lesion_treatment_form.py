import streamlit as st
from modules.i18n.i18n import t


def render_lesion_treatment_form(
    tratamientos_list,
    tratamientos_default,
    personal_reporte_text,
    descripcion_text,
    disabled_edit
):

    col1, col2 = st.columns([2,1])

    with col1:
        tipo_tratamiento = st.multiselect(
            t("Tipo(s) de tratamiento"),
            options=tratamientos_list,
            default=tratamientos_default,
            placeholder="Selecciona uno o más",
            max_selections=5,
            disabled=disabled_edit,
            key=f"tipo_tratamiento_{st.session_state['form_version']}"
        )

    with col2:
        personal_reporta = st.text_input(
            t("Personal médico que reporta *"),
            value=personal_reporte_text,
            disabled=disabled_edit,
            key=f"personal_reporta_{st.session_state['form_version']}"
        )

    descripcion = st.text_area(
        t("Observaciones / Descripción de la lesión"),
        value=descripcion_text,
        disabled=disabled_edit,
        key=f"descripcion_{st.session_state['form_version']}"
    )

    return {
        "tipo_tratamiento": tipo_tratamiento,
        "personal_reporta": personal_reporta,
        "descripcion": descripcion
    }