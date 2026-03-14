import streamlit as st
import datetime
from modules.i18n.i18n import t


def render_lesion_clinical_form(
    diagnostico_text,
    es_recidiva_value,
    tipos_recidiva,
    idx_tipo_recidiva,
    placeholder,
    fecha_alta_diagnostico_date,
    disabled_edit
):

    form_version = st.session_state["form_version"]

    diagnostico = st.text_area(
        t("Diagnóstico Médico"),
        disabled=disabled_edit,
        value=diagnostico_text,
        key=f"diagnostico_{form_version}"
    )

    col1, col2, col3, col4 = st.columns([1, 2.5, 1, 2.5])

    # ------------------------------------------------
    # Recidiva
    # ------------------------------------------------

    with col1:
        es_recidiva = st.checkbox(
            t("Es Recidiva"),
            value=es_recidiva_value,
            disabled=disabled_edit,
            key=f"es_recidiva_{form_version}"
        )

    with col2:
        tipo_recidiva = st.selectbox(
            t("Tipo de recidiva (según tiempo desde el alta anterior)"),
            options=tipos_recidiva if es_recidiva else ["NO APLICA"],
            index=idx_tipo_recidiva,
            disabled=(not es_recidiva) or disabled_edit,
            placeholder=placeholder,
            key=f"tipo_recidiva_{form_version}"
        )

    # ------------------------------------------------
    # Baja deportiva
    # ------------------------------------------------

    with col3:

        implica_baja_value = bool(fecha_alta_diagnostico_date)

        implica_baja = st.checkbox(
            t("Implica Baja"),
            value=implica_baja_value,
            disabled=disabled_edit,
            key=f"implica_baja_{form_version}"
        )

    # ------------------------------------------------
    # Fecha alta deportiva
    # ------------------------------------------------

    with col4:
        key_fecha = f"fecha_alta_diagnostico_{form_version}"

        if implica_baja:

            if fecha_alta_diagnostico_date:
                fecha_default = fecha_alta_diagnostico_date
            else:
                fecha_default = datetime.date.today() + datetime.timedelta(days=1)

            if key_fecha not in st.session_state or st.session_state[key_fecha] in (None, ""):
                st.session_state[key_fecha] = fecha_default

            fecha_alta_diagnostico = st.date_input(
                t("Alta Deportiva (estimada)"),
                disabled=disabled_edit,
                key=key_fecha
            )

        else:
            st.session_state[key_fecha] = None

            st.date_input(
                t("Alta Deportiva (estimada)"),
                disabled=True,
                key=key_fecha
            )

            fecha_alta_diagnostico = None

    return {
        "diagnostico": diagnostico,
        "es_recidiva": es_recidiva,
        "tipo_recidiva": tipo_recidiva,
        "implica_baja": implica_baja,
        "fecha_alta_diagnostico": fecha_alta_diagnostico,
    }