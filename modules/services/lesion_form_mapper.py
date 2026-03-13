from modules.models.lesion_form_model import LesionFormModel


def build_lesion_form_model(
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
):

    return LesionFormModel(
        fecha_lesion=fecha_str,
        lugar_id=lugar_id,
        segmento_id=segmento_id,
        zona_cuerpo_id=zona_cuerpo_id,
        zona_especifica_id=zona_especifica_id,
        lateralidad=lateralidad,
        tipo_lesion_id=tipo_lesion_id,
        tipo_especifico_id=tipo_especifico_id,
        es_recidiva=es_recidiva,
        tipo_recidiva=tipo_recidiva,
        dias_baja_estimado=dias_baja_estimado,
        gravedad=gravedad,
        mecanismo_id=mecanismo_id,
        tratamientos=tratamientos_str,
        personal_reporta=personal_reporta,
        fecha_alta_diagnostico=fecha_alta_diagnostico_str,
        estado_lesion=estado_lesion,
        diagnostico=diagnostico,
        descripcion=descripcion
    )