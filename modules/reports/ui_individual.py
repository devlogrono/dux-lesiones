
import streamlit as st
import plotly.express as px
import pandas as pd
from modules.i18n.i18n import t

from modules.util.util import (get_photo, clean_image_url, calcular_edad)

def player_block_dux(jugadora_seleccionada: dict, unavailable="N/A"):
    """Muestra el bloque visual con la información principal de la jugadora."""

    # Validar jugadora seleccionada
    if not jugadora_seleccionada or not isinstance(jugadora_seleccionada, dict):
        st.info(t("Selecciona una jugadora para continuar."))
        st.stop()
    
    #st.dataframe(jugadora_seleccionada)
    # Extraer información básica
    nombre_completo = jugadora_seleccionada.get("nombre_jugadora", unavailable).strip().capitalize()
    #apellido = jugadora_seleccionada.get("apellido", "").strip().upper()
    #nombre_completo = f"{nombre.capitalize()} {apellido.capitalize()}"
    id_jugadora = jugadora_seleccionada.get("id_jugadora", unavailable)
    posicion = jugadora_seleccionada.get("posicion", unavailable)
    pais = jugadora_seleccionada.get("nacionalidad", unavailable)
    fecha_nac = jugadora_seleccionada.get("fecha_nacimiento", unavailable)
    genero = jugadora_seleccionada.get("genero", "")
    competicion = jugadora_seleccionada.get("plantel", "")
    dorsal = jugadora_seleccionada.get("dorsal", "")
    url_drive = jugadora_seleccionada.get("foto_url", "")

    dorsal_number = f":red[/ Dorsal #{int(dorsal)}]" if pd.notna(dorsal) else ""

    # Calcular edad
    edad_texto, fnac = calcular_edad(fecha_nac)

    # Color temático
    #color = "violet" if genero.upper() == "F" else "blue"

    # Icono de género
    if genero.upper() == "F":
        genero_icono = ":material/girl:"
        profile_image = "female"
    elif genero.upper() == "H":
        genero_icono = ":material/boy:"
        profile_image = "male"
    else:
        genero_icono = ""
        profile_image = "profile"

    # Bloque visual
    st.markdown(f"### {nombre_completo.title()} {dorsal_number}")
    #st.markdown(f"##### **_:red[Identificación:]_** _{id_jugadora}_ | **_:red[País:]_** _{pais.upper()}_")

    col1, col2, col3 = st.columns([1.6, 2, 2])

    with col1:
        if pd.notna(url_drive) and url_drive and url_drive != "No Disponible":
            direct_url = clean_image_url(url_drive)
            #st.text(direct_url)
            response = get_photo(direct_url)
            if response and response.status_code == 200 and 'image' in response.headers.get("Content-Type", ""):
                st.image(response.content, width=300)
            else:
                st.image(f"assets/images/{profile_image}.png", width=300)
        else:
            st.image(f"assets/images/{profile_image}.png", width=300)

    with col2:
        #st.markdown(f"**:material/sports_soccer: Competición:** {competicion}")
        #st.markdown(f"**:material/cake: Fecha Nac.:** {fecha_nac}")

        st.metric(label=t(":red[:material/id_card: Identificación]"), value=f"{id_jugadora}", border=True)
        st.metric(label=t(":red[:material/sports_soccer: Plantel]"), value=f"{competicion}", border=True)
        st.metric(label=t(":red[:material/cake: F. Nacimiento]"), value=f"{fecha_nac}", border=True)
                    
    with col3:
        #st.markdown(f"**:material/person: Posición:** {posicion.capitalize()}")
        #st.markdown(f"**:material/favorite: Edad:** {edad if edad != unavailable else 'N/A'} años")

        st.metric(label=t(":red[:material/globe: País]"), value=f"{pais if pais else 'N/A'}", border=True)
        st.metric(label=t(":red[:material/person: Posición]"), value=f"{posicion.capitalize() if posicion else 'N/A'}", border=True)
        st.metric(label=t(":red[:material/favorite: Edad]"), value=f"{edad_texto}", border=True)
          
    st.divider()


def render_active_injury_progress(df_periodo: pd.DataFrame):
    import pandas as pd
    import streamlit as st
    from modules.i18n.i18n import t

    if df_periodo is None or df_periodo.empty:
        return

    required_cols = {"estado_lesion", "fecha_lesion"}
    if not required_cols.issubset(df_periodo.columns):
        return

    df_act = df_periodo.copy()
    df_act["fecha_lesion"] = pd.to_datetime(df_act["fecha_lesion"], errors="coerce")

    if "dias_baja_estimado" in df_act.columns:
        df_act["dias_baja_estimado"] = pd.to_numeric(df_act["dias_baja_estimado"], errors="coerce")
    else:
        df_act["dias_baja_estimado"] = pd.NA

    df_act = df_act[
        df_act["estado_lesion"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .eq("ACTIVO")
    ].copy()

    df_act = df_act.dropna(subset=["fecha_lesion"])

    if df_act.empty:
        return

    # Lesión activa más reciente
    lesion = df_act.sort_values("fecha_lesion", ascending=False).iloc[0]

    hoy = pd.Timestamp.today().normalize()
    fecha_lesion = pd.to_datetime(lesion["fecha_lesion"]).normalize()
    dias_transcurridos = max((hoy - fecha_lesion).days, 0)

    dias_estimados = lesion.get("dias_baja_estimado", pd.NA)
    dias_estimados = None if pd.isna(dias_estimados) else float(dias_estimados)

    tipo = str(lesion.get("tipo_lesion", "-")).strip() if pd.notna(lesion.get("tipo_lesion", None)) else "-"
    zona = str(lesion.get("zona_cuerpo", "-")).strip() if pd.notna(lesion.get("zona_cuerpo", None)) else "-"

    st.markdown(f"### {t('Seguimiento de lesión activa')}")

    if dias_estimados is None or dias_estimados <= 0:
        st.info(
            f"**{tipo}** · **{zona}**  \n"
            f"{t('Fecha lesión')}: {fecha_lesion.strftime('%d/%m/%Y')}  \n"
            f"{t('Días transcurridos')}: {dias_transcurridos}"
        )
        return

    dias_restantes = max(round(dias_estimados - dias_transcurridos, 1), 0)
    progreso = min(dias_transcurridos / dias_estimados, 1.0) if dias_estimados > 0 else 0
    pct = round(progreso * 100)

    st.markdown(
        f"**{tipo}** · **{zona}**  \n"
        f"{t('Fecha lesión')}: {fecha_lesion.strftime('%d/%m/%Y')}  \n"
        f"{t('Evolución estimada')}: **{dias_transcurridos} / {dias_estimados:g} {t('días')}**  \n"
        f"{t('Restan estimados')}: **{dias_restantes:g} {t('días')}**"
    )

    st.markdown(
        f"<div style='text-align:center; font-weight:600; margin-bottom:0.25rem;'>{pct}%</div>",
        unsafe_allow_html=True
    )
    st.progress(progreso)



def grafico_evolucion_lesiones(df: pd.DataFrame):
    """Muestra una línea temporal de lesiones con color por gravedad y tamaño según días de baja."""
    if df.empty:
        return None

    df = df.copy()
    df["fecha_lesion"] = pd.to_datetime(df["fecha_lesion"], errors="coerce")

    # Filtrar solo las columnas que existen
    hover_cols = [col for col in ["tipo_lesion", "zona_cuerpo", "mecanismo", "descripcion"] if col in df.columns]

    fig = px.scatter(
        df.sort_values("fecha_lesion"),
        x="fecha_lesion",
        y="dias_baja_estimado",
        color="impacto_dias_baja_estimado",
        size="dias_baja_estimado",
        hover_data=hover_cols,
        title=t("Evolución temporal de lesiones con baja"),
        color_discrete_map={
            "LEVE": "#b7e4c7",
            "MODERADA": "#f4d35e",
            "GRAVE": "#ee924b",
            "MUY GRAVE": "#d62828",
        },
        category_orders={
            "impacto_dias_baja_estimado": ["LEVE", "MODERADA", "GRAVE", "MUY GRAVE"]
        }
    )

    # Palitos del lollipop
    for _, row in df.iterrows():
        fig.add_shape(
            type="line",
            x0=row["fecha_lesion"],
            x1=row["fecha_lesion"],
            y0=0,
            y1=row["dias_baja_estimado"],
            line=dict(color="rgba(120,120,120,0.45)", width=2),
            layer="below"
        )

    fig.update_traces(marker=dict(sizemin=8))

    fig.update_layout(
        xaxis_title=t("Fecha de lesión"),
        yaxis_title=t("Días de baja estimados"),
        template="simple_white",
        height=400
    )
    return fig


def grafico_zonas_lesionadas(df: pd.DataFrame):
    """Bar chart horizontal de zonas corporales más lesionadas."""
    if df.empty:
        return None

    zonas = df["zona_cuerpo"].value_counts().reset_index()
    zonas.columns = ["Zona corporal", "Frecuencia"]

    fig = px.bar(
        zonas,
        x="Frecuencia",
        y="Zona corporal",
        orientation="h",
        color="Frecuencia",
        color_continuous_scale="Reds",
        title=t("Zonas corporales más lesionadas")
    )
    fig.update_layout(template="simple_white", height=400)
    return fig

def grafico_tipo_mecanismo(df: pd.DataFrame):
    """Comparación entre tipo de lesión y mecanismo."""
    if df.empty:
        return None

    data = df.copy()
    data["tipo_lesion"] = data["tipo_lesion"].fillna("N/A").astype(str).str.strip()
    data["mecanismo"] = data["mecanismo"].fillna("N/A").astype(str).str.strip()

    resumen = (
        data.groupby(["tipo_lesion", "mecanismo"])
        .size()
        .reset_index(name="total")
    )

    resumen["label"] = resumen["total"].apply(lambda x: str(int(x)) if x > 0 else "")

    fig = px.bar(
        resumen,
        x="tipo_lesion",
        y="total",
        color="mecanismo",
        barmode="stack",
        text="label",
        title=t("Relación entre tipo de lesión y mecanismo"),
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle"
    )

    fig.update_layout(
        xaxis_title=t("Tipo de lesión"),
        yaxis_title=t("Frecuencia"),
        template="simple_white",
        height=400
    )

    return fig


from collections import Counter

def grafico_tipo_tratamiento(df: pd.DataFrame):
    """Relación entre tipo de lesión y tratamiento aplicado."""
    if df.empty or "tipo_lesion" not in df.columns or "tipo_tratamiento" not in df.columns:
        return None

    data = df.copy()
    data["tipo_lesion"] = data["tipo_lesion"].fillna("N/A").astype(str).str.strip()

    rows = []
    for _, row in data.iterrows():
        tipo = row["tipo_lesion"]
        tratamientos = row.get("tipo_tratamiento", None)

        if isinstance(tratamientos, list):
            tr_list = [str(x).strip() for x in tratamientos if str(x).strip()]
        elif isinstance(tratamientos, str) and tratamientos.strip():
            tr_list = [x.strip() for x in tratamientos.split(",") if x.strip()]
        else:
            tr_list = []

        for tr in tr_list:
            rows.append({"tipo_lesion": tipo, "tratamiento": tr})

    if not rows:
        return None

    df_tr = pd.DataFrame(rows)

    resumen = (
        df_tr.groupby(["tipo_lesion", "tratamiento"])
        .size()
        .reset_index(name="total")
    )

    resumen["label"] = resumen["total"].apply(lambda x: str(int(x)) if x > 0 else "")

    fig = px.bar(
        resumen,
        x="tipo_lesion",
        y="total",
        color="tratamiento",
        barmode="stack",
        text="label",
        title=t("Relación entre tipo de lesión y tratamiento")
    )

    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle"
    )

    fig.update_layout(
        xaxis_title=t("Tipo de lesión"),
        yaxis_title=t("Frecuencia"),
        template="simple_white",
        height=420
    )

    return fig

from collections import Counter

def grafico_tipo_zona_tratamiento(df: pd.DataFrame):
    """Sunburst de tipo de lesión -> zona corporal -> tratamiento."""
    if (
        df is None or df.empty
        or "tipo_lesion" not in df.columns
        or "zona_cuerpo" not in df.columns
        or "tipo_tratamiento" not in df.columns
    ):
        return None

    data = df.copy()
    data["tipo_lesion"] = data["tipo_lesion"].fillna("N/A").astype(str).str.strip()
    data["zona_cuerpo"] = data["zona_cuerpo"].fillna("N/A").astype(str).str.strip()

    rows = []
    for _, row in data.iterrows():
        tipo = row["tipo_lesion"]
        zona = row["zona_cuerpo"]
        tratamientos = row.get("tipo_tratamiento", None)

        if isinstance(tratamientos, list):
            tr_list = [str(x).strip() for x in tratamientos if str(x).strip()]
        elif isinstance(tratamientos, str) and tratamientos.strip():
            tr_list = [x.strip() for x in tratamientos.split(",") if x.strip()]
        else:
            tr_list = []

        if not tr_list:
            rows.append({
                "tipo_lesion": tipo,
                "zona_cuerpo": zona,
                "tratamiento": "N/A",
            })
        else:
            for tr in tr_list:
                rows.append({
                    "tipo_lesion": tipo,
                    "zona_cuerpo": zona,
                    "tratamiento": tr,
                })

    if not rows:
        return None

    df_plot = pd.DataFrame(rows)

    resumen = (
        df_plot.groupby(["tipo_lesion", "zona_cuerpo", "tratamiento"])
        .size()
        .reset_index(name="frecuencia")
    )

    fig = px.sunburst(
        resumen,
        path=["tipo_lesion", "zona_cuerpo", "tratamiento"],
        values="frecuencia",
        title=t("Relación entre tipo de lesión, zona y tratamiento")
    )

    fig.update_layout(
        template="simple_white",
        height=520
    )

    return fig

def grafico_dias_baja(df: pd.DataFrame):
    """Boxplot que muestra la distribución de días de baja por nivel de impacto o severidad."""
    if df.empty:
        return None

    fig = px.box(
        df,
        x="impacto_dias_baja_estimado",
        y="dias_baja_estimado",
        color="impacto_dias_baja_estimado",
        title=t("Días de baja según impacto o severidad"),
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig.update_layout(
        xaxis_title="Impacto o Severidad",
        yaxis_title="Días de baja",
        template="simple_white",
        height=400
    )
    return fig

def grafico_recidivas(df: pd.DataFrame):
    """Pie chart de proporción de lesiones recidivantes vs nuevas."""
    if df.empty or "es_recidiva" not in df.columns:
        return None

    conteo = df["es_recidiva"].map({True: "Recidiva", False: "Nueva"}).value_counts().reset_index()
    conteo.columns = ["Tipo", "Frecuencia"]

    fig = px.pie(
        conteo,
        names="Tipo",
        values="Frecuencia",
        color="Tipo",
        color_discrete_sequence=px.colors.qualitative.Set2,
        title=t("Proporción de recidivas vs nuevas")
    )
    fig.update_layout(template="simple_white", height=350)
    return fig

def grafico_tipo_recidiva(df: pd.DataFrame):
    """Relación entre tipo de lesión y recidiva, con zona corporal en el hover."""
    if (
        df is None or df.empty
        or "tipo_lesion" not in df.columns
        or "es_recidiva" not in df.columns
    ):
        return None

    data = df.copy()
    data["tipo_lesion"] = (
        data["tipo_lesion"]
        .fillna("N/A")
        .astype(str)
        .str.strip()
    )

    data["tipo_caso"] = (
        data["es_recidiva"]
        .fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "si", "sí"])
        .map({True: t("Recidiva"), False: t("Nueva")})
    )

    if "zona_cuerpo" in data.columns:
        data["zona_cuerpo"] = (
            data["zona_cuerpo"]
            .fillna("N/A")
            .astype(str)
            .str.strip()
        )
    else:
        data["zona_cuerpo"] = "N/A"

    resumen = (
        data.groupby(["tipo_lesion", "tipo_caso"])
        .agg(
            total=("tipo_lesion", "size"),
            zonas=("zona_cuerpo", lambda s: ", ".join(sorted(set([z for z in s if z]))))
        )
        .reset_index()
    )

    orden_tipos = (
        resumen.groupby("tipo_lesion")["total"]
        .sum()
        .sort_values(ascending=True)
        .index
        .tolist()
    )

    resumen["tipo_lesion"] = pd.Categorical(
        resumen["tipo_lesion"],
        categories=orden_tipos,
        ordered=True
    )

    resumen["tipo_caso"] = pd.Categorical(
        resumen["tipo_caso"],
        categories=[t("Nueva"), t("Recidiva")],
        ordered=True
    )

    resumen["label"] = resumen["total"].apply(lambda x: str(int(x)) if x > 0 else "")

    fig = px.bar(
        resumen.sort_values(["tipo_lesion", "tipo_caso"]),
        x="total",
        y="tipo_lesion",
        color="tipo_caso",
        orientation="h",
        barmode="stack",
        text="label",
        hover_data={
            "total": True,
            "zonas": True,
            "tipo_lesion": False,
            "tipo_caso": False,
        },
        title=t("Relación entre tipo de lesión y recidiva"),
        color_discrete_map={
            t("Nueva"): "#9ecae1",
            t("Recidiva"): "#d62728",
        }
    )

    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle"
    )

    fig.update_layout(
        template="simple_white",
        height=420,
        xaxis_title=t("Número de lesiones"),
        yaxis_title="",
        legend_title_text=""
    )

    return fig
