import streamlit as st
from modules.ui.forms.lesion_treatment_form import render_lesion_treatment_form
from modules.i18n.i18n import t
from modules.ui.forms.lesion_clinical_form import render_lesion_clinical_form
from modules.services.lesion_form_mapper import build_lesion_form_model
from modules.services.catalog_service import load_lesion_catalogs
from modules.services.lesion_form_state import build_form_state
from modules.services.lesion_logic_service import (calcular_estado_lesion, calcular_gravedad)
from modules.ui.forms.lesion_basic_form import render_lesion_basic_form
from modules.services.lesion_record_builder import (build_new_lesion_record,update_lesion_record)
from modules.ui.forms.lesion_evolution_form import render_lesion_evolution_form
from modules.services.lesion_validation_service import (validate_lesion_form)
from modules.util.ui_helpers import preview_record
import json

from modules.util.util import normalize_text

def view_registro_lesion(modo: str = "nuevo", jugadora_info: str = None, lesion_data = None) -> None:

    #st.text(lesion_data)
    error = False
    # -------------------------
    # Inicialización segura evolución
    # -------------------------

    alta_medica = False
    alta_deportiva = False

    fecha_alta_medica = None
    fecha_alta_deportiva = None

    alta_medica_value = False
    alta_deportiva_value = False

    placeholder=t("Selecciona una opción")
    default_list=[t("NO APLICA")]

    if "form_version" not in st.session_state:
        st.session_state["form_version"] = 0

    disabled_edit = False
    rol = st.session_state["auth"]["rol"].lower()

    if lesion_data and lesion_data.get("estado_lesion") == "INACTIVO":
        disabled_edit = True
    elif modo == "editar" and rol not in ("admin", "developer"):
        disabled_edit = True

    disabled_evolution = False
    
    if lesion_data and lesion_data["estado_lesion"] == "INACTIVO":
        fecha_alta_medica = lesion_data.get("fecha_alta_medica", None)
        fecha_alta_deportiva = lesion_data.get("fecha_alta_deportiva", None)
        fecha_observacion_activa = lesion_data.get("fecha_observacion_activa", None)
        fecha_observacion_inactiva = lesion_data.get("fecha_observacion_inactiva", None)
        
        disabled_evolution = True

        info = []

        if fecha_alta_medica:
            info.append(f"{t('fecha de alta médica')}: {fecha_alta_medica}")

        if fecha_alta_deportiva:
            info.append(f"{t('fecha de alta deportiva')}: {fecha_alta_deportiva}")

        if info:
            st.warning(f"{t('La lesión está **Inactiva**')} ({', '.join(info)}).")
        else:
            st.warning(t("La lesión se encuentra en estado **Inactiva**."))

    lesion_help =t("Lesiones agrupadas según el tejido afectado y mecanismo (criterios FIFA/UEFA).")
    
    catalogs = load_lesion_catalogs()

    segmentos_corporales_df = catalogs["segmentos_df"]
    segmentos_corporales_list = catalogs["segmentos_list"]
    map_segmentos_nombre_a_id = catalogs["map_segmentos"]

    zonas_segmento_df = catalogs["zonas_segmento_df"]
    map_zonas_segmento_nombre_a_id = catalogs["map_zonas_segmento"]

    zonas_anatomicas_df = catalogs["zonas_anatomicas_df"]
    map_zonas_anatomicas_nombre_a_id = catalogs["map_zonas_anatomicas"]

    mecanismos_df = catalogs["mecanismos_df"]
    mecanismo_list = catalogs["mecanismos_list"]
    map_mecanismos_nombre_a_id = catalogs["map_mecanismos"]

    tipos_lesion_df = catalogs["tipos_df"]
    map_tipo_nombre_a_id = catalogs["map_tipos"]

    subtipos_df = catalogs["subtipos_df"]
    map_subtipos_nombre_a_id = catalogs["map_subtipos"]

    relacion_df = catalogs["relacion_df"]

    tratamientos_list = catalogs["tratamientos_list"]

    lugares_list = catalogs["lugares_list"]
    map_lugares_nombre_a_id = catalogs["map_lugares"]

    lateralidades = catalogs["lateralidades"]
    tipos_recidiva = catalogs["tipos_recidiva"]

    gravedad_dias = catalogs["gravedad_dias"]
    ############## BD DATA ##############

    form_state = build_form_state(
        modo,
        lesion_data,
        tratamientos_list,
        segmentos_corporales_list,
        lugares_list,
        mecanismo_list,
        lateralidades,
        tipos_recidiva
    )
    #st.text(f"form_state {form_state}")
    fecha_lesion_date = form_state["fecha_lesion_date"]
    fecha_alta_diagnostico_date = form_state["fecha_alta_diagnostico_date"]
    fecha_observacion_activa_date = form_state["fecha_observacion_activa_date"]
    fecha_observacion_inactiva_date = form_state["fecha_observacion_inactiva_date"]

    diagnostico_text = form_state["diagnostico_text"]
    descripcion_text = form_state["descripcion_text"]
    personal_reporte_text = form_state["personal_reporte_text"]

    dias_baja_estimado = form_state["dias_baja_estimado"]
    tratamientos_default = form_state["tratamientos_default"]

    idx_segmento = form_state["idx_segmento"]
    idx_lugar = form_state["idx_lugar"]
    idx_mecanismo = form_state["idx_mecanismo"]
    idx_lateralidad = form_state["idx_lateralidad"]
    idx_tipo_recidiva = form_state["idx_tipo_recidiva"]

    es_recidiva_value = form_state.get("es_recidiva_value", False)
    alta_medica_value = form_state.get("alta_medica_value", False)
    alta_deportiva_value = form_state.get("alta_deportiva_value", False)

    st.caption(t(":red[Los campos marcados con * son obligatorios.]"))

    #############################################
    basic_data = render_lesion_basic_form(
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
    )

    fecha_lesion = basic_data["fecha_lesion"]
    fecha_str = fecha_lesion.strftime("%Y-%m-%d")
    lugar = basic_data["lugar"]
    mecanismo_lesion = basic_data["mecanismo_lesion"]
    tipo_lesion = basic_data["tipo_lesion"]
    tipo_especifico = basic_data["tipo_especifico"]
    segmento = basic_data["segmento"]
    zona_cuerpo = basic_data["zona_cuerpo"]
    zona_especifica = basic_data["zona_especifica"]
    lateralidad = basic_data["lateralidad"]

    clinical_data = render_lesion_clinical_form(
        diagnostico_text,
        es_recidiva_value,
        tipos_recidiva,
        idx_tipo_recidiva,
        placeholder,
        fecha_alta_diagnostico_date,
        disabled_edit
    )

    diagnostico = clinical_data["diagnostico"]
    es_recidiva = clinical_data["es_recidiva"]
    tipo_recidiva = clinical_data["tipo_recidiva"]
    implica_baja = clinical_data["implica_baja"]
    fecha_alta_diagnostico = clinical_data["fecha_alta_diagnostico"]
        
    dias_baja_estimado, estado_lesion, error_estado = calcular_estado_lesion(
        fecha_lesion,
        fecha_alta_diagnostico,
        implica_baja,
        fecha_observacion_activa_date,
        lesion_data
    )

    if error_estado:
        error = True
        st.warning(t(":material/warning: La fecha de alta no puede ser anterior a la fecha de registro."))

    st.info(f"{t(':material/calendar_clock: Días estimados de baja:')} {dias_baja_estimado} {t('día(s)')}")

    gravedad, rango = calcular_gravedad(dias_baja_estimado, gravedad_dias)

    if gravedad:
        texto_rango = f"{t(':material/personal_injury: Severidad o Impacto de la lesión según los días de baja:')} **{gravedad}**"
        st.warning(texto_rango)

    treatment_data = render_lesion_treatment_form(
        tratamientos_list,
        tratamientos_default,
        personal_reporte_text,
        descripcion_text,
        disabled_edit
    )

    tipo_tratamiento = treatment_data["tipo_tratamiento"]
    personal_reporta = treatment_data["personal_reporta"]
    descripcion = treatment_data["descripcion"]
    

    ############## FIN LOGICA ##############

    if modo == "editar":

        evolution_data = render_lesion_evolution_form(
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
        )

        record_evolucion = evolution_data["record_evolucion"]
        alta_medica = evolution_data["alta_medica"]
        alta_deportiva = evolution_data["alta_deportiva"]
        fecha_alta_medica = evolution_data["fecha_alta_medica"]
        fecha_alta_deportiva = evolution_data["fecha_alta_deportiva"]

        #st.text(f"evolution {evolution_data}")
        if evolution_data["error"]:
            #st.text(error)
            error = True

    ############# PROCESAMIENTO Y GUARDADO #############  
    tratamientos_str = ([t.upper() for t in tipo_tratamiento] if isinstance(tipo_tratamiento, list) else [])

    errors_form = validate_lesion_form(
        lugar,
        segmento,
        zona_cuerpo,
        tipo_lesion,
        mecanismo_lesion,
        personal_reporta
    )
    #st.text(errors_form)
    if errors_form:
        error = True

    # -------------------------
    # Preparar IDs para el record
    # -------------------------

    lugar_id = map_lugares_nombre_a_id.get(lugar)
    segmento_id = map_segmentos_nombre_a_id.get(segmento)

    zona_cuerpo_id = map_zonas_segmento_nombre_a_id.get(zona_cuerpo)
    zona_especifica_id = map_zonas_anatomicas_nombre_a_id.get(zona_especifica)

    tipo_lesion_id = map_tipo_nombre_a_id.get(tipo_lesion)
    tipo_especifico_id = map_subtipos_nombre_a_id.get(tipo_especifico)

    mecanismo_id = map_mecanismos_nombre_a_id.get(mecanismo_lesion)

    # -------------------------
    # Fecha alta diagnóstico
    # -------------------------

    fecha_alta_diagnostico_str = (
        fecha_alta_diagnostico.strftime("%Y-%m-%d")
        if fecha_alta_diagnostico
        else None
    )

    form_model = build_lesion_form_model(
        fecha_str,
        lugar_id,
        segmento_id,
        zona_cuerpo_id,
        zona_especifica_id,
        lateralidad,
        tipo_lesion_id,
        tipo_especifico_id,
        es_recidiva,
        tipo_recidiva,
        dias_baja_estimado,
        gravedad,
        mecanismo_id,
        tratamientos_str,
        personal_reporta,
        fecha_alta_diagnostico_str,
        estado_lesion,
        diagnostico,
        descripcion
    )

    record = build_new_lesion_record(
            jugadora_info,
            form_model,
            st.session_state['auth']['username']
        )

    if modo == "editar": 

        ##conservar identificadores originales
        record["id"] = lesion_data["id"]
        record["id_lesion"] = lesion_data["id_lesion"]
        
        #conservar evolución existente
        record["evolucion"] = lesion_data.get("evolucion", [])

        record = update_lesion_record(
            record,
            record_evolucion,
            alta_medica,
            fecha_alta_medica,
            alta_deportiva,
            fecha_alta_deportiva
        )


    if st.session_state["auth"]["rol"].lower() == "developer":
        st.divider()
        if st.checkbox(t("Previsualización")):
            preview_record(record)
            #st.caption(f"Datos almacenados en: {DATA_DIR}/registros.jsonl")

    if error:
        st.error(t("Existen campos obligatorios que debe seleccionar"))

   # ---------------------------------
    # detectar cambios en formulario
    # ---------------------------------

    form_compare = {
        "fecha_lesion": form_model.fecha_lesion or "",
        "lugar_id": form_model.lugar_id,
        "segmento_id": form_model.segmento_id,
        "zona_cuerpo_id": form_model.zona_cuerpo_id,
        "zona_especifica_id": form_model.zona_especifica_id,
        "lateralidad": normalize_text(form_model.lateralidad),
        "tipo_lesion_id": form_model.tipo_lesion_id,
        "tipo_especifico_id": form_model.tipo_especifico_id,
        "mecanismo_id": form_model.mecanismo_id,
        "es_recidiva": bool(form_model.es_recidiva),
        "tratamientos": sorted([x.upper() for x in (form_model.tratamientos or [])]),
        "diagnostico": normalize_text(form_model.diagnostico),
        "descripcion": normalize_text(form_model.descripcion),
        "personal_reporta": normalize_text(form_model.personal_reporta),
        "tipo_recidiva": normalize_text(form_model.tipo_recidiva),
        "estado_lesion": form_model.estado_lesion or "",
        "fecha_alta_diagnostico": form_model.fecha_alta_diagnostico or "",
    }

    form_snapshot = json.dumps(form_compare, sort_keys=True, ensure_ascii=False)

    form_changed = False
    original_snapshot = None

    if modo == "editar":
        original_compare = {
            "fecha_lesion": lesion_data.get("fecha_lesion") or "",
            "lugar_id": map_lugares_nombre_a_id.get(lesion_data.get("lugar")),
            "segmento_id": map_segmentos_nombre_a_id.get(lesion_data.get("segmento")),
            "zona_cuerpo_id": map_zonas_segmento_nombre_a_id.get(lesion_data.get("zona_cuerpo")),
            "zona_especifica_id": map_zonas_anatomicas_nombre_a_id.get(lesion_data.get("zona_especifica")),
            "lateralidad": normalize_text(lesion_data.get("lateralidad")),
            "tipo_lesion_id": map_tipo_nombre_a_id.get(lesion_data.get("tipo_lesion")),
            "tipo_especifico_id": map_subtipos_nombre_a_id.get(lesion_data.get("tipo_especifico")),
            "mecanismo_id": map_mecanismos_nombre_a_id.get(lesion_data.get("mecanismo")),
            "es_recidiva": bool(lesion_data.get("es_recidiva")),
            "tratamientos": sorted([x.upper() for x in (lesion_data.get("tipo_tratamiento") or [])]),
            "diagnostico": normalize_text(lesion_data.get("diagnostico")),
            "descripcion": normalize_text(lesion_data.get("descripcion")),
            "personal_reporta": normalize_text(lesion_data.get("personal_reporta")),
            "tipo_recidiva": normalize_text(lesion_data.get("tipo_recidiva")),
            "estado_lesion": lesion_data.get("estado_lesion") or "",
            "fecha_alta_diagnostico": lesion_data.get("fecha_alta_diagnostico") or "",
        }

        original_snapshot = json.dumps(original_compare, sort_keys=True, ensure_ascii=False)
        form_changed = form_snapshot != original_snapshot
    # ---------------------------------
    # detectar cambios en evolución
    # ---------------------------------

    evolucion_changed = False

    if modo == "editar" and record_evolucion:
        evolucion_changed = any([
            bool(record_evolucion.get("tratamiento_aplicado")),
            bool((record_evolucion.get("personal_seguimiento") or "").strip()),
            bool((record_evolucion.get("observaciones") or "").strip()),
        ])

    # DEBUG temporal
    # st.write("1 - FORM_SNAPSHOT:", form_snapshot)
    # st.write("2 - ORIGINAL_SNAPSHOT:", original_snapshot if modo == "editar" else None)
    # st.write("3 - FORM_CHANGED:", form_changed)
    #st.write("4- EVOLUCION_CHANGED:", evolucion_changed)

    return record, error, disabled_evolution, form_changed, evolucion_changed, disabled_edit