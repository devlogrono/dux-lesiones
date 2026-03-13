import streamlit as st
import datetime
from modules.i18n.i18n import t


def render_lesion_basic_form(
    modo,
    lesion_data,
    fecha_lesion_date,
    segmentos_corporales_list,
    lugares_list,
    mecanismo_list,
    lateralidades,
    idx_segmento,
    idx_lugar,
    idx_mecanismo,
    idx_lateralidad,
    zonas_segmento_df,
    zonas_anatomicas_df,
    mecanismos_df,
    tipos_lesion_df,
    subtipos_df,
    relacion_df,
    map_segmentos_nombre_a_id,
    map_zonas_segmento_nombre_a_id,
    map_tipo_nombre_a_id,
    default_list,
    placeholder,
    lesion_help,
    disabled_edit,
):
    form_v = st.session_state["form_version"]

    col1, col2, col3, col4, col5 = st.columns(5)

    # --------------------------------
    # COL 1
    # --------------------------------
    with col1:

        fecha_lesion = st.date_input(
            t("Fecha de la lesión *"),
            fecha_lesion_date,
            disabled=disabled_edit,
            max_value=datetime.date.today(),
            key=f"fecha_lesion_{form_v}",
        )

        segmento = st.selectbox(
            t("Región anatómica *"),
            segmentos_corporales_list,
            index=idx_segmento,
            disabled=disabled_edit,
            placeholder=placeholder,
            key=f"segmento_{form_v}",
        )

    # --------------------------------
    # COL 2
    # --------------------------------
    with col2:

        lugar = st.selectbox(
            t("Lugar *"),
            lugares_list,
            index=idx_lugar,
            disabled=disabled_edit,
            placeholder=placeholder,
            key=f"lugar_{form_v}",
        )

        idx_zonas = 0

        if segmento:
            segmento_id = map_segmentos_nombre_a_id.get(segmento)
            zonas_segmento_filtrados = zonas_segmento_df[
                zonas_segmento_df["segmento_id"] == segmento_id
            ]
            zonas_segmento_list = zonas_segmento_filtrados["nombre"].tolist()
        else:
            zonas_segmento_list = []

        opciones_tipo_zona = zonas_segmento_list if zonas_segmento_list else default_list
        is_disabled = disabled_edit or not zonas_segmento_list

        if modo == "editar":
            try:
                idx_zonas = zonas_segmento_list.index(lesion_data["zona_cuerpo"])
            except Exception:
                idx_zonas = 0

        zona_cuerpo = st.selectbox(
            t("Zona anatómica *"),
            opciones_tipo_zona,
            index=idx_zonas,
            disabled=is_disabled,
            placeholder=placeholder,
            key=f"zona_cuerpo_{form_v}",
        )

    # --------------------------------
    # COL 3
    # --------------------------------
    with col3:

        mecanismo_lesion = st.selectbox(
            t("Mecanismo de lesión *"),
            mecanismo_list,
            index=idx_mecanismo,
            disabled=disabled_edit,
            placeholder=placeholder,
            key=f"mecanismo_lesion_{form_v}",
        )

        idx_zona_espec = 0

        if zona_cuerpo:
            zonas_segmento_id = map_zonas_segmento_nombre_a_id.get(zona_cuerpo)

            zonas_anatomicas_filtrados = zonas_anatomicas_df[
                zonas_anatomicas_df["zona_id"] == zonas_segmento_id
            ]

            zonas_anatomicas_list = zonas_anatomicas_filtrados["nombre"].tolist()

        else:
            zonas_anatomicas_list = []

        opciones_tipo_zona_especifica = (
            zonas_anatomicas_list if zonas_anatomicas_list else default_list
        )

        is_disabled = disabled_edit or not zonas_anatomicas_list

        if modo == "editar":
            try:
                idx_zona_espec = zonas_anatomicas_list.index(
                    lesion_data["zona_especifica"]
                )
            except Exception:
                idx_zona_espec = 0

        zona_especifica = st.selectbox(
            t("Estructura anatómica *"),
            opciones_tipo_zona_especifica,
            index=idx_zona_espec,
            key=f"subregion_{form_v}",
            disabled=is_disabled,
            placeholder=placeholder,
        )

    # --------------------------------
    # COL 4
    # --------------------------------
    with col4:

        idx_tipos_lesion = 0

        if mecanismo_lesion:

            mecanismo_id = mecanismos_df.loc[
                mecanismos_df["nombre"] == mecanismo_lesion, "id"
            ].iloc[0]

            tipos_filtrados = tipos_lesion_df.merge(
                relacion_df[relacion_df["mecanismo_id"] == mecanismo_id],
                left_on="id",
                right_on="tipo_lesion_id",
                how="inner",
            )

            tipos_lesion_list = tipos_filtrados["nombre"].drop_duplicates().tolist()

        else:
            tipos_lesion_list = []

        opciones_tipo_lesion = tipos_lesion_list if tipos_lesion_list else default_list
        is_disabled = disabled_edit or not tipos_lesion_list

        if modo == "editar":
            try:
                idx_tipos_lesion = tipos_lesion_list.index(
                    lesion_data.get("tipo_lesion", "")
                )
            except Exception:
                idx_tipos_lesion = 0

        tipo_lesion = st.selectbox(
            t("Tipo de lesión *"),
            opciones_tipo_lesion,
            index=idx_tipos_lesion,
            disabled=is_disabled,
            help=lesion_help,
            placeholder=placeholder,
            key=f"tipo_lesion_{form_v}",
        )

        lateralidad = st.selectbox(
            t("Lateralidad"),
            lateralidades,
            index=idx_lateralidad,
            disabled=disabled_edit,
            placeholder=placeholder,
            key=f"lateralidad_{form_v}",
        )

    # --------------------------------
    # COL 5
    # --------------------------------
    with col5:

        idx_tipo_especifico = 0

        if mecanismo_lesion and tipo_lesion:

            tipo_lesion_id = map_tipo_nombre_a_id.get(tipo_lesion)

            relaciones_validas = relacion_df[
                (relacion_df["mecanismo_id"] == mecanismo_id)
                & (relacion_df["tipo_lesion_id"] == tipo_lesion_id)
            ]

            subtipos_ids = (
                relaciones_validas["tipo_especifico_id"].dropna().astype(int).tolist()
            )

            if subtipos_ids:
                subtipos_filtrados = subtipos_df[subtipos_df["id"].isin(subtipos_ids)]
                subtipos_list = subtipos_filtrados["nombre"].tolist()
                is_disabled = False
            else:
                subtipos_list = []
                is_disabled = True

        else:
            subtipos_list = []
            is_disabled = True

        opciones_tipo = subtipos_list if subtipos_list else default_list
        is_disabled = disabled_edit or not subtipos_list

        if modo == "editar" and subtipos_list:
            try:
                idx_tipo_especifico = subtipos_list.index(
                    lesion_data.get("tipo_especifico", "")
                )
            except Exception:
                idx_tipo_especifico = 0

        tipo_especifico = st.selectbox(
            t("Tipo específico *"),
            opciones_tipo,
            index=idx_tipo_especifico,
            disabled=is_disabled,
            help=lesion_help,
            placeholder=placeholder,
            key=f"tipo_especifico_{form_v}",
        )

    return {
        "fecha_lesion": fecha_lesion,
        "lugar": lugar,
        "mecanismo_lesion": mecanismo_lesion,
        "tipo_lesion": tipo_lesion,
        "tipo_especifico": tipo_especifico,
        "segmento": segmento,
        "zona_cuerpo": zona_cuerpo,
        "zona_especifica": zona_especifica,
        "lateralidad": lateralidad,
    }