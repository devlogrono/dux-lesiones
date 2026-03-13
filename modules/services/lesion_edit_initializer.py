from modules.util.util import is_valid
from modules.util.util import parse_fecha


def init_edit_mode(
    lesion_data,
    segmentos_corporales_list,
    lugares_list,
    mecanismo_list,
    lateralidades,
    tipos_recidiva,
):
    """
    Inicializa todos los valores necesarios cuando el formulario
    se abre en modo editar.
    """

    fecha_lesion_date = parse_fecha(lesion_data["fecha_lesion"])
    fecha_alta_diagnostico_date = parse_fecha(lesion_data["fecha_alta_diagnostico"])

    fecha_observacion_activa_date = parse_fecha(lesion_data["fecha_observacion_activa"])
    fecha_observacion_inactiva_date = parse_fecha(lesion_data["fecha_observacion_inactiva"])

    fecha_alta_medica = lesion_data.get("fecha_alta_medica")
    fecha_alta_deportiva = lesion_data.get("fecha_alta_deportiva")

    alta_medica_value = bool(is_valid(fecha_alta_medica))
    alta_deportiva_value = bool(is_valid(fecha_alta_deportiva))

    if not alta_medica_value:
        fecha_alta_medica = None

    if not alta_deportiva_value:
        fecha_alta_deportiva = None

    diagnostico_text = lesion_data.get("diagnostico", "")
    descripcion_text = lesion_data.get("descripcion", "")
    personal_reporte_text = lesion_data.get("personal_reporta", "")
    dias_baja_estimado = int(lesion_data.get("dias_baja_estimado", 0))

    es_recidiva_value = lesion_data.get("es_recidiva")

    def safe_index(lst, value):
        try:
            return lst.index(value)
        except Exception:
            lst.append(value)
            return lst.index(value)

    idx_segmento = safe_index(segmentos_corporales_list, lesion_data.get("segmento"))
    idx_lugar = safe_index(lugares_list, lesion_data.get("lugar"))
    idx_mecanismo = safe_index(mecanismo_list, lesion_data.get("mecanismo"))
    idx_lateralidad = safe_index(lateralidades, lesion_data.get("lateralidad"))
    idx_tipo_recidiva = safe_index(tipos_recidiva, lesion_data.get("tipo_recidiva"))

    return {
        "fecha_lesion_date": fecha_lesion_date,
        "fecha_alta_diagnostico_date": fecha_alta_diagnostico_date,
        "fecha_observacion_activa_date": fecha_observacion_activa_date,
        "fecha_observacion_inactiva_date": fecha_observacion_inactiva_date,
        "fecha_alta_medica": fecha_alta_medica,
        "fecha_alta_deportiva": fecha_alta_deportiva,
        "alta_medica_value": alta_medica_value,
        "alta_deportiva_value": alta_deportiva_value,
        "diagnostico_text": diagnostico_text,
        "descripcion_text": descripcion_text,
        "personal_reporte_text": personal_reporte_text,
        "dias_baja_estimado": dias_baja_estimado,
        "es_recidiva_value": es_recidiva_value,
        "idx_segmento": idx_segmento,
        "idx_lugar": idx_lugar,
        "idx_mecanismo": idx_mecanismo,
        "idx_lateralidad": idx_lateralidad,
        "idx_tipo_recidiva": idx_tipo_recidiva,
    }