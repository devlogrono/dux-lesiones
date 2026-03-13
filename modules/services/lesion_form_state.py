import datetime
from modules.util.ui_helpers import safe_index
from modules.util.util import is_valid, parse_fecha, get_normalized_treatment


def build_form_state(modo, lesion_data, tratamientos_list,
                     segmentos_corporales_list, lugares_list,
                     mecanismo_list, lateralidades, tipos_recidiva):
    """
    Construye el estado inicial del formulario dependiendo del modo (nuevo / editar).
    """

    state = {}

    if modo == "editar":

        state["fecha_lesion_date"] = parse_fecha(lesion_data["fecha_lesion"])
        state["fecha_alta_diagnostico_date"] = parse_fecha(lesion_data["fecha_alta_diagnostico"])

        state["fecha_observacion_activa_date"] = parse_fecha(lesion_data["fecha_observacion_activa"])
        state["fecha_observacion_inactiva_date"] = parse_fecha(lesion_data["fecha_observacion_inactiva"])

        fecha_alta_medica = lesion_data.get("fecha_alta_medica")
        fecha_alta_deportiva = lesion_data.get("fecha_alta_deportiva")

        state["alta_medica_value"] = bool(is_valid(fecha_alta_medica))
        state["alta_deportiva_value"] = bool(is_valid(fecha_alta_deportiva))

        state["diagnostico_text"] = lesion_data.get("diagnostico", "")
        state["descripcion_text"] = lesion_data.get("descripcion", "")
        state["personal_reporte_text"] = lesion_data.get("personal_reporta", "")

        state["dias_baja_estimado"] = int(lesion_data.get("dias_baja_estimado", 0))

        tratamientos_default = get_normalized_treatment(lesion_data)
        state["tratamientos_default"] = [t for t in tratamientos_default if t in tratamientos_list]

        state["es_recidiva_value"] = lesion_data.get("es_recidiva")

        # índices seguros
        state["idx_segmento"] = safe_index(segmentos_corporales_list, lesion_data.get("segmento"))
        state["idx_lugar"] = safe_index(lugares_list, lesion_data.get("lugar"))
        state["idx_mecanismo"] = safe_index(mecanismo_list, lesion_data.get("mecanismo"))
        state["idx_lateralidad"] = safe_index(lateralidades, lesion_data.get("lateralidad"))
        state["idx_tipo_recidiva"] = safe_index(tipos_recidiva, lesion_data.get("tipo_recidiva"))

    else:

        state["fecha_lesion_date"] = datetime.date.today()
        state["fecha_alta_diagnostico_date"] = None
        state["fecha_observacion_activa_date"] = None
        state["fecha_observacion_inactiva_date"] = None

        state["idx_segmento"] = None
        state["idx_lugar"] = None
        state["idx_mecanismo"] = None
        state["idx_lateralidad"] = None
        state["idx_tipo_recidiva"] = None

        state["es_recidiva_value"] = None

        state["diagnostico_text"] = ""
        state["descripcion_text"] = ""
        state["personal_reporte_text"] = ""

        state["dias_baja_estimado"] = 0
        state["tratamientos_default"] = []

    return state