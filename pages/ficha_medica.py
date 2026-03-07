import streamlit as st
import datetime
import modules.app_config.config as config
config.init_config()

from modules.ui.ui_components import selection_header

st.header("Ficha :red[médica]", divider=True)

# --- Filtros de datos ---
jugadora_seleccionada, posicion, records = selection_header(modo=2)
st.divider()

# --- Bloque de jugadora seleccionada ---
#player_block_dux(jugadora_seleccionada)
st.divider()

if jugadora_seleccionada:
    st.subheader("Registro de Información Médica", divider=True)

    col1, col2 = st.columns(2)
    with col1:
        fecha = st.date_input("Fecha de registro", datetime.date.today())
        medico = st.text_input("Nombre del médico responsable")
        centro = st.text_input("Centro o institución médica")
        motivo = st.text_input("Motivo de la consulta o evaluación")
    with col2:
        altura = st.number_input("Altura (cm)", min_value=100, max_value=220, step=1)
        peso = st.number_input("Peso (kg)", min_value=30, max_value=120, step=1)
        presion = st.text_input("Presión arterial (ej: 120/80 mmHg)")
        fc_reposo = st.number_input("Frecuencia cardíaca en reposo (lpm)", min_value=40, max_value=200)

    st.divider()

    st.subheader("🧠 Antecedentes Médicos")
    col1, col2 = st.columns(2)
    with col1:
        enfermedad_cronica = st.selectbox(
            "¿Padece alguna enfermedad crónica?",
            ["No", "Sí"]
        )
        if enfermedad_cronica == "Sí":
            detalle_enfermedad = st.text_area("Indique cuál(es):")
        else:
            detalle_enfermedad = ""

        medicamentos = st.selectbox(
            "¿Toma actualmente algún medicamento?",
            ["No", "Sí"]
        )
        if medicamentos == "Sí":
            detalle_medicamentos = st.text_area("Detalle los medicamentos y dosis:")
        else:
            detalle_medicamentos = ""
    with col2:
        alergias = st.selectbox("¿Tiene alergias?", ["No", "Sí"])
        if alergias == "Sí":
            detalle_alergias = st.text_area("Indique a qué es alérgica:")
        else:
            detalle_alergias = ""

        operaciones = st.selectbox("¿Ha sido operada?", ["No", "Sí"])
        if operaciones == "Sí":
            detalle_operaciones = st.text_area("Indique tipo de cirugía y año:")
        else:
            detalle_operaciones = ""

    st.divider()

    st.subheader("⚕️ Evaluación Actual")
    col1, col2 = st.columns(2)
    with col1:
        dolor_actual = st.select_slider("Nivel de dolor actual (EVA)", options=range(0, 11), value=0)
        lesion_activa = st.selectbox("¿Presenta alguna lesión activa?", ["No", "Sí"])
        if lesion_activa == "Sí":
            descripcion_lesion = st.text_area("Describa la lesión actual:")
        else:
            descripcion_lesion = ""
    with col2:
        en_tratamiento = st.selectbox("¿Se encuentra bajo tratamiento médico?", ["No", "Sí"])
        if en_tratamiento == "Sí":
            detalle_tratamiento = st.text_area("Detalle el tratamiento actual:")
        else:
            detalle_tratamiento = ""

    st.divider()
    observaciones = st.text_area("🩶 Observaciones generales y recomendaciones:")

    st.divider()

    guardar = st.button("Guardar registro médico")

    if guardar:
        registro = {
            "jugadora": jugadora_seleccionada,
            "posicion": posicion,
            "fecha": str(fecha),
            "medico": medico,
            "centro": centro,
            "motivo": motivo,
            "altura_cm": altura,
            "peso_kg": peso,
            "presion": presion,
            "fc_reposo": fc_reposo,
            "enfermedad_cronica": enfermedad_cronica,
            "detalle_enfermedad": detalle_enfermedad,
            "medicamentos": medicamentos,
            "detalle_medicamentos": detalle_medicamentos,
            "alergias": alergias,
            "detalle_alergias": detalle_alergias,
            "operaciones": operaciones,
            "detalle_operaciones": detalle_operaciones,
            "dolor_actual": dolor_actual,
            "lesion_activa": lesion_activa,
            "descripcion_lesion": descripcion_lesion,
            "en_tratamiento": en_tratamiento,
            "detalle_tratamiento": detalle_tratamiento,
            "observaciones": observaciones,
            "fecha_registro": str(datetime.datetime.now())
        }

        st.success("✅ Registro médico guardado correctamente.")
        st.json(registro)

else:
    st.info("Selecciona una jugadora para registrar o consultar su ficha médica.")
