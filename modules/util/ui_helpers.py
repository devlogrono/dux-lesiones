import json
import streamlit as st
from modules.i18n.i18n import t

def safe_index(lst, value):
    """
    Devuelve el índice de un valor dentro de una lista.
    Si el valor no existe lo añade para evitar errores
    en formularios de edición.
    """
    if value is None:
        return 0

    try:
        return lst.index(value)
    except ValueError:
        lst.append(value)
        return lst.index(value)
    
    
def preview_record(record: dict) -> None:
    #st.subheader("Previsualización")
    # Header with key fields
    #jug = record.get("nombre", "-")
    fecha = record.get("fecha_hora", "-")
    posicion = record.get("posicion", "-")
    tipo = record.get("tipo_lesion", "-")
    #st.markdown(f"**Jugadora:** {jug}  |  **Fecha:** {fecha}  |  **Posicion:** {posicion}  |  **Tipo Lesión:** {tipo}")
    with st.expander(t("Ver registro JSON"), expanded=True):
        st.code(json.dumps(record, ensure_ascii=False, indent=2), language="json")

