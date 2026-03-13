from modules.util.util import is_valid


def build_evolution_state(
    estado_lesion,
    fecha_observacion_activa,
    fecha_observacion_inactiva,
    fecha_alta_medica,
    fecha_alta_deportiva,
):
    """
    Determina el estado actual de la lesión según fechas y evolución.
    """

    disabled_evolution = False

    if estado_lesion == "inactivo":
        disabled_evolution = True

    if is_valid(fecha_alta_deportiva):
        estado_lesion = "inactivo"

    elif is_valid(fecha_observacion_inactiva):
        estado_lesion = "observacion"

    elif is_valid(fecha_observacion_activa):
        estado_lesion = "activo"

    return {
        "estado_lesion": estado_lesion,
        "disabled_evolution": disabled_evolution,
    }

def build_evolution_record(
    estado_lesion,
    fecha_observacion_activa,
    fecha_observacion_inactiva,
    fecha_alta_medica,
    fecha_alta_deportiva,
):
    """
    Construye el JSON de evolución de lesión.
    """

    record_evolucion = {
        "estado_lesion": estado_lesion,
        "fecha_observacion_activa": fecha_observacion_activa,
        "fecha_observacion_inactiva": fecha_observacion_inactiva,
        "fecha_alta_medica": fecha_alta_medica,
        "fecha_alta_deportiva": fecha_alta_deportiva,
    }

    return record_evolucion