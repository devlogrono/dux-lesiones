from modules.util.util import date_to_str
import datetime


import datetime


def build_new_lesion_record(
    jugadora_info,
    form_model,
    username,
):
    """
    Construye el record de lesión para inserción usando LesionFormModel.
    """

    return {
        "id_lesion": None,
        "id_jugadora": jugadora_info["id_jugadora"],
        "nombre": jugadora_info["nombre_completo"],
        "posicion": jugadora_info["posicion"].upper(),

        "fecha_lesion": form_model.fecha_lesion,

        "lugar_id": form_model.lugar_id,
        "segmento_id": form_model.segmento_id,
        "zona_cuerpo_id": form_model.zona_cuerpo_id,
        "zona_especifica_id": form_model.zona_especifica_id,

        "lateralidad": form_model.lateralidad,

        "tipo_lesion_id": form_model.tipo_lesion_id,
        "tipo_especifico_id": form_model.tipo_especifico_id,

        "es_recidiva": form_model.es_recidiva,
        "tipo_recidiva": form_model.tipo_recidiva,

        "dias_baja_estimado": form_model.dias_baja_estimado,
        "impacto_dias_baja_estimado": form_model.gravedad,

        "mecanismo_id": form_model.mecanismo_id,

        "tipo_tratamiento": form_model.tratamientos,

        "personal_reporta": form_model.personal_reporta,

        "fecha_alta_diagnostico": form_model.fecha_alta_diagnostico,

        "fecha_alta_medica": None,
        "fecha_alta_deportiva": None,

        "fecha_observacion_activa": None,
        "fecha_observacion_inactiva": None,

        "estado_lesion": form_model.estado_lesion,

        "diagnostico": form_model.diagnostico,
        "descripcion": form_model.descripcion,

        "evolucion": [],

        "fecha_hora_registro": datetime.datetime.now().isoformat(),

        "usuario": username,
    }


def update_lesion_record(
    lesion_data,
    record_evolucion,
    alta_medica,
    fecha_alta_medica,
    alta_deportiva,
    fecha_alta_deportiva,
):
    """
    Actualiza una lesión existente con evolución.
    """

    if "evolucion" not in lesion_data or not isinstance(lesion_data["evolucion"], list):
        lesion_data["evolucion"] = []

    tiene_datos = any([
        record_evolucion["tratamiento_aplicado"],
        record_evolucion["personal_seguimiento"],
        record_evolucion["observaciones"]
    ])

    if tiene_datos:
        lesion_data["evolucion"].append(record_evolucion)

    if alta_medica and fecha_alta_medica:
        lesion_data["fecha_alta_medica"] = fecha_alta_medica.strftime("%Y-%m-%d")
        lesion_data["fecha_alta_deportiva"] = None

    if lesion_data.get("fecha_alta_deportiva") is None and fecha_alta_deportiva:
        if alta_deportiva and fecha_alta_deportiva:
            lesion_data["fecha_alta_deportiva"] = fecha_alta_deportiva.strftime("%Y-%m-%d")
            lesion_data["estado_lesion"] = "INACTIVO"

    lesion_data["fecha_observacion_activa"] = date_to_str(lesion_data["fecha_observacion_activa"])
    lesion_data["fecha_observacion_inactiva"] = date_to_str(lesion_data["fecha_observacion_inactiva"])

    return lesion_data