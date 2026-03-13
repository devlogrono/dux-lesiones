import json

import pandas as pd
import streamlit as st
from modules.i18n.i18n import t
from modules.db.db_catalogs import load_catalog_list_db
from modules.util.io_files import load_catalog_list
from modules.util.util import get_normalized_treatment, parse_fecha

def view_registro_lesion_read(jugadora_info: dict, lesion_data: dict):

    default_list = [t("NO APLICA")]

    lesion_help = t("Lesiones agrupadas según el tejido afectado y mecanismo (criterios FIFA/UEFA).")

    ############################
    # CATÁLOGOS
    ############################

    segmentos_corporales_df = load_catalog_list_db("segmentos_corporales", as_df=True)
    segmentos_corporales_list = segmentos_corporales_df["nombre"].tolist()

    zonas_segmento_df = load_catalog_list_db("zonas_segmento", as_df=True)

    zonas_anatomicas_df = load_catalog_list_db("zonas_anatomicas", as_df=True)

    mecanismos_df = load_catalog_list_db("mecanismos", as_df=True)
    mecanismo_list = mecanismos_df["nombre"].tolist()

    tipos_lesion_df = load_catalog_list_db("tipo_lesion", as_df=True)

    subtipos_df = load_catalog_list_db("tipo_especifico_lesion", as_df=True)

    relacion_df = load_catalog_list_db("mecanismo_tipo_lesion", as_df=True)

    tratamientos_df = load_catalog_list_db("tratamientos", as_df=True)
    tratamientos_list = tratamientos_df["nombre"].tolist()

    lugares_df = load_catalog_list_db("lugares", as_df=True)
    lugares_list = lugares_df["nombre"].tolist()

    lateralidades = load_catalog_list("lateralidades")
    tipos_recidiva = load_catalog_list("tipos_recidiva")

    ############################
    # VALORES DESDE DB
    ############################

    fecha_lesion = parse_fecha(lesion_data["fecha_lesion"])

    segmento = lesion_data.get("segmento")
    lugar = lesion_data.get("lugar")
    mecanismo = lesion_data.get("mecanismo")
    lateralidad = lesion_data.get("lateralidad")

    zona_cuerpo = lesion_data.get("zona_cuerpo")
    zona_especifica = lesion_data.get("zona_especifica")

    tipo_lesion = lesion_data.get("tipo_lesion")
    tipo_especifico = lesion_data.get("tipo_especifico")

    diagnostico = lesion_data.get("diagnostico", "")
    descripcion = lesion_data.get("descripcion", "")

    tratamientos_default = get_normalized_treatment(lesion_data)

    es_recidiva = lesion_data.get("es_recidiva")
    tipo_recidiva = lesion_data.get("tipo_recidiva")

    personal_reporta = lesion_data.get("personal_reporta")

    dias_baja_estimado = lesion_data.get("dias_baja_estimado", 0)

    ############################
    # UI
    ############################

    #st.caption(t(":red[Los campos marcados con * son obligatorios.]"))

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:

        st.date_input(
            t("Fecha de la lesión "),
            value=fecha_lesion,
            disabled=True
        )

        st.selectbox(
            t("Región anatómica "),
            segmentos_corporales_list,
            index=segmentos_corporales_list.index(segmento) if segmento in segmentos_corporales_list else 0,
            disabled=True
        )

    with col2:

        st.selectbox(
            t("Lugar "),
            lugares_list,
            index=lugares_list.index(lugar) if lugar in lugares_list else 0,
            disabled=True
        )

        zonas_segmento_list = zonas_segmento_df["nombre"].tolist()

        st.selectbox(
            t("Zona anatómica "),
            zonas_segmento_list if zonas_segmento_list else default_list,
            index=zonas_segmento_list.index(zona_cuerpo) if zona_cuerpo in zonas_segmento_list else 0,
            disabled=True
        )

    with col3:

        st.selectbox(
            t("Mecanismo de lesión "),
            mecanismo_list,
            index=mecanismo_list.index(mecanismo) if mecanismo in mecanismo_list else 0,
            disabled=True
        )

        zonas_anatomicas_list = zonas_anatomicas_df["nombre"].tolist()

        st.selectbox(
            t("Estructura anatómica "),
            zonas_anatomicas_list if zonas_anatomicas_list else default_list,
            index=zonas_anatomicas_list.index(zona_especifica) if zona_especifica in zonas_anatomicas_list else 0,
            disabled=True
        )

    with col4:

        tipos_lesion_list = tipos_lesion_df["nombre"].tolist()

        st.selectbox(
            t("Tipo de lesión "),
            tipos_lesion_list if tipos_lesion_list else default_list,
            index=tipos_lesion_list.index(tipo_lesion) if tipo_lesion in tipos_lesion_list else 0,
            disabled=True,
            help=lesion_help
        )

        st.selectbox(
            t("Lateralidad"),
            lateralidades,
            index=lateralidades.index(lateralidad) if lateralidad in lateralidades else 0,
            disabled=True
        )

    with col5:

        subtipos_list = subtipos_df["nombre"].tolist()

        st.selectbox(
            t("Tipo específico "),
            subtipos_list if subtipos_list else default_list,
            index=subtipos_list.index(tipo_especifico) if tipo_especifico in subtipos_list else 0,
            disabled=True,
            help=lesion_help
        )

    ############################

    st.text_area(
        t("Diagnóstico Médico"),
        value=diagnostico,
        disabled=True
    )

    col1, col2, col3, col4 = st.columns([1,2.5,1,2.5])

    with col1:

        st.checkbox(
            t("Es Recidiva"),
            value=es_recidiva,
            disabled=True
        )

    with col2:

        st.selectbox(
            t("Tipo de recidiva"),
            tipos_recidiva,
            index=tipos_recidiva.index(tipo_recidiva) if tipo_recidiva in tipos_recidiva else 0,
            disabled=True
        )

    with col3:

        st.checkbox(
            t("Implica Baja"),
            value=dias_baja_estimado > 0,
            disabled=True
        )

    with col4:

        st.number_input(
            t("Días estimados de baja"),
            value=dias_baja_estimado,
            disabled=True
        )

    st.info(f"{t(':material/calendar_clock: Días estimados de baja:')} {dias_baja_estimado}")

    ############################

    col1, col2 = st.columns([2,1])

    with col1:

        st.multiselect(
            t("Tipo(s) de tratamiento"),
            options=tratamientos_list,
            default=tratamientos_default,
            disabled=True
        )

    with col2:

        st.text_input(
            t("Personal médico que reporta "),
            value=personal_reporta,
            disabled=True
        )

    st.text_area(
        t("Observaciones / Descripción de la lesión"),
        value=descripcion,
        disabled=True
    )

    ############################
    # HISTORIAL
    ############################

    show_evolucion_historial_read(lesion_data) 

def show_evolucion_historial_read(lesion_data: dict):
    """
    Muestra únicamente el historial de evolución de una lesión (modo lectura).
    Replica la lógica de show_evolucion_historial pero sin inputs ni edición.
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
        df_evol["fecha_control"] = (
            pd.to_datetime(df_evol["fecha_control"], errors="coerce")
            .dt.date
        )

    if "fecha_hora_registro" in df_evol.columns:
        df_evol["fecha_hora_registro"] = pd.to_datetime(
            df_evol["fecha_hora_registro"], errors="coerce"
        )

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
            "fecha_control",
            "tratamiento_aplicado",
            "personal_seguimiento",
            "observaciones",
            "usuario",
            "fecha_hora_registro",
        ]
        if c in df_evol.columns
    ]

    df_evol = df_evol[columnas_orden]

    # 8. Mostrar resultados
    st.divider()
    st.markdown(t("### Historial"))

    num_sesiones = len(df_evol)
    st.caption(f"{t('Total de sesiones registradas:')} **{num_sesiones}**")

    st.dataframe(df_evol, hide_index=True)