from modules.util.util import get_gravedad_por_dias
import streamlit as st

def calcular_estado_lesion(
    fecha_lesion,
    fecha_alta_diagnostico,
    implica_baja,
    fecha_observacion_activa_date,
    lesion_data,
):
    """
    Determina estado de la lesión y días estimados de baja.
    No depende de Streamlit.
    """
    #st.text(f"fecha_alta_diagnostico {fecha_alta_diagnostico}")
    if fecha_alta_diagnostico and (fecha_alta_diagnostico - fecha_lesion).days < 0:
        return None, None, True

    if not fecha_observacion_activa_date:

        if implica_baja:
            dias_baja_estimado = max(0, (fecha_alta_diagnostico - fecha_lesion).days)
            estado_lesion = "ACTIVO"
        else:
            dias_baja_estimado = 0
            estado_lesion = "OBSERVACION"

    else:
        dias_baja_estimado = lesion_data.get("dias_baja_estimado", 0)
        estado_lesion = lesion_data["estado_lesion"]

    return dias_baja_estimado, estado_lesion, False


def calcular_gravedad(dias_baja_estimado, gravedad_dias):
    """
    Determina gravedad de la lesión según días de baja.
    """
    gravedad, rango = get_gravedad_por_dias(dias_baja_estimado, gravedad_dias)
    return gravedad, rango