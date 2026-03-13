from modules.util.util import is_valid


def validate_lesion_form(
    lugar,
    segmento,
    zona_cuerpo,
    tipo_lesion,
    mecanismo_lesion,
    personal_reporta,
):
    """
    Valida los campos obligatorios del formulario de lesión.
    """

    errors = []

    if not lugar:
        errors.append("lugar")

    if not segmento:
        errors.append("segmento")

    if not zona_cuerpo:
        errors.append("zona_cuerpo")

    if not tipo_lesion:
        errors.append("tipo_lesion")

    if not mecanismo_lesion:
        errors.append("mecanismo")

    if not personal_reporta or not personal_reporta.strip():
        errors.append("personal_reporta")

    return errors

def validate_evolution_form(seguimiento, personal_seguimiento):

    errors = []

    if seguimiento:
        if not personal_seguimiento or not personal_seguimiento.strip():
            errors.append("personal_seguimiento")

    return errors