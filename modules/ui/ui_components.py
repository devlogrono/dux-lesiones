import streamlit as st
import datetime
import pandas as pd

from modules.db.db_competitions import load_competitions_db
from modules.db.db_players import load_players_db
from modules.i18n.i18n import t
import pandas as pd
import json

from modules.db.db_records import load_lesiones_db
from modules.util.schema import MAP_POSICIONES

def load_posiciones_traducidas() -> dict:
    return {key: t(valor_es) for key, valor_es in MAP_POSICIONES.items()}

def selection_header(modo: int = 1):
    ALL_TEXT = t("Todas")

    jug_df = load_players_db()   

    if jug_df.empty:
        st.info("No se encontraron registros de jugadoras.")
        st.stop()

    comp_df = load_competitions_db()
   
    if modo == 1:
        col1, col2, col3 = st.columns([2,1,2])
    else:
        records = load_lesiones_db() 
        
        if records.empty:    
            st.warning(t("No hay datos de lesiones disponibles."))
            st.stop()   
        col1, col2, col3, col4 = st.columns([2,1.3,2,1])

    with col1:
        competiciones_options = comp_df.to_dict("records")
        competicion = st.selectbox(
            t("Plantel"),
            options=competiciones_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            placeholder=t("Seleccione un plantel"),
            index=3,
        )
        
    with col2:
        MAP_POSICIONES_TRADUCIDAS = load_posiciones_traducidas()
        MAP_POSICIONES_INVERTIDO = {v: k for k, v in MAP_POSICIONES_TRADUCIDAS.items()}

        posicion_traducida = st.selectbox(
            t("Posición"),
            options=list(MAP_POSICIONES_TRADUCIDAS.values()),
            placeholder=t("Seleccione una Posición"),
            index=None
        )
        
        clave = MAP_POSICIONES_INVERTIDO.get(posicion_traducida)
        posicion = MAP_POSICIONES.get(clave)
        
        filtro_actual = (
            competicion["codigo"] if competicion else None,
            posicion
        )

        if st.session_state.get("last_filtro_jugadora") != filtro_actual:
            st.session_state.pop("jugadora_nombre", None)
            st.session_state["last_filtro_jugadora"] = filtro_actual
    with col3:
        if competicion:
            codigo_competicion = competicion["codigo"]
            jug_df_filtrado = jug_df[jug_df["plantel"] == codigo_competicion]
        else:
            jug_df_filtrado = jug_df.copy()

        if posicion:
            jug_df_filtrado = jug_df_filtrado[
                jug_df_filtrado["posicion"] == posicion
            ]

        # Lista estable de nombres
        jugadora_nombres = (
            jug_df_filtrado["nombre_jugadora"]
            .astype(str)
            .sort_values()
            .tolist()
        )

        # Resolver índice (permite vacío)
        jugadora_index = None
        if (
            "jugadora_nombre" in st.session_state
            and st.session_state["jugadora_nombre"] in jugadora_nombres
        ):
            jugadora_index = jugadora_nombres.index(
                st.session_state["jugadora_nombre"]
            )

        jugadora_nombre = st.selectbox(
            t("Jugadora"),
            options=jugadora_nombres,
            format_func=lambda x: f"{jugadora_nombres.index(x) + 1} - {x}",
            index=jugadora_index,
            placeholder=t("Seleccione una Jugadora"),
            key="jugadora_selector_lesiones"
        )

        # Persistir selección
        if jugadora_nombre:
            st.session_state["jugadora_nombre"] = jugadora_nombre
        else:
            st.session_state.pop("jugadora_nombre", None)

        # Reconstruir objeto completo solo si hay selección
        jugadora_seleccionada = None
        if "jugadora_nombre" in st.session_state:
            jugadora_seleccionada = jug_df_filtrado[
                jug_df_filtrado["nombre_jugadora"].astype(str)
                == st.session_state["jugadora_nombre"]
            ].iloc[0].to_dict()

    #st.dataframe(jug_df_filtrado)
    if modo >= 2:
        with col4:
            # Filtrado por jugadora seleccionada
            if jugadora_seleccionada:
                records = records[records["id_jugadora"] == jugadora_seleccionada["id_jugadora"]]
            else:
                if modo == 2:
                    records = pd.DataFrame()
                elif modo == 3:

                    # modo >= 3 → filtrar por todas las jugadoras del plantel o posición
                    if not jug_df_filtrado.empty and "id_jugadora" in jug_df_filtrado.columns:
                        ids_validos = jug_df_filtrado["id_jugadora"].astype(str).tolist()
                        records = records[records["id_jugadora"].astype(str).isin(ids_validos)]
                    else:
                        records = pd.DataFrame()

            # Verificar si hay registros
            if records.empty:
                selected_tipo = st.selectbox(
                t("Tipo de lesión"),
                [t("NO APLICA")],
                disabled=True)
            else:
                # Mostrar filtro activo si hay registros
                tipos = sorted(records["tipo_lesion"].dropna().unique())
                selected_tipo = st.selectbox(
                    t("Tipo de lesión"),
                    tipos,
                    index=None,
                    disabled=False,
                    placeholder="Seleccione un opción"
                )

                if selected_tipo and selected_tipo != ALL_TEXT:
                    records = records[records["tipo_lesion"] == selected_tipo]

   
    jug_df_filtrado = jug_df_filtrado if "jug_df_filtrado" in locals() else pd.DataFrame()

    #st.dataframe(records)
    # Si no hay jugadoras en ese plantel o posición
    if jug_df_filtrado.empty:
        #st.warning("⚠️ No hay jugadoras disponibles para este plantel o posición seleccionada.")
        jugadora_seleccionada = None
        if modo == 1:
            return None, posicion
        else:
            return None, posicion, pd.DataFrame()  # Devuelve vacío

    if modo == 1:
        return jugadora_seleccionada, posicion
    else:
        return jugadora_seleccionada, posicion, records


def data_filters_advanced():
    ALL_TEXT = t("TODAS")

    # --- Cargar datos ---
    jug_df = load_players_db()

    if jug_df is None or "plantel" not in jug_df.columns:
        st.error(t("No se pudo cargar la lista de jugadoras o falta la columna 'plantel'."))
        st.stop()

    comp_df = load_competitions_db()
    records = load_lesiones_db()

    if records.empty:
        st.warning(t("No hay datos de lesiones disponibles."))
        st.stop()

    if jug_df.empty or records.empty:
        st.warning(t("No hay datos disponibles para aplicar filtros."))
        return None, None, None, None, (None, None), pd.DataFrame()

    # --- Preparación fechas ---
    records = records.copy()
    records["fecha_lesion"] = pd.to_datetime(records["fecha_lesion"], errors="coerce")
    records = records.dropna(subset=["fecha_lesion"]).copy()

    if records.empty:
        st.warning(t("No hay fechas válidas de lesión para aplicar filtros."))
        return None, None, None, None, (None, None), pd.DataFrame()

    min_date_base = records["fecha_lesion"].min().date()
    max_date_base = records["fecha_lesion"].max().date()

    hoy = datetime.date.today()
    fecha_ref_natural = hoy
    inicio_temporada = datetime.date(2025, 7, 16)

    # --- Layout ---
    col1, col2, col3, col4, col5 = st.columns([3, 1.5, 1.6, 1.8, 2.2])

    # --- FILTRO 1: Plantel ---
    with col1:
        competiciones_options = comp_df.to_dict("records") if comp_df is not None else []
        competicion = st.selectbox(
            t("Plantel"),
            options=competiciones_options,
            format_func=lambda x: f'{x["nombre"]} ({x["codigo"]})',
            placeholder=t("Seleccione un plantel"),
            index=3
        )

    # --- FILTRO 2: Posición ---
    with col2:
        MAP_POSICIONES_TRADUCIDAS = load_posiciones_traducidas()
        MAP_POSICIONES_INVERTIDO = {v: k for k, v in MAP_POSICIONES_TRADUCIDAS.items()}

        posicion_traducida = st.selectbox(
            t("Posición"),
            options=[ALL_TEXT] + list(MAP_POSICIONES_TRADUCIDAS.values()),
            placeholder=t("Seleccione una Posición"),
            index=0
        )

        if posicion_traducida == ALL_TEXT:
            posicion = ALL_TEXT
        else:
            clave = MAP_POSICIONES_INVERTIDO.get(posicion_traducida)
            posicion = MAP_POSICIONES.get(clave)

    # --- Filtrar jugadoras por plantel y posición ---
    jugadoras_filtradas = jug_df.copy()

    if competicion:
        codigo_competicion = competicion["codigo"]
        jugadoras_filtradas = jugadoras_filtradas[
            jugadoras_filtradas["plantel"] == codigo_competicion
        ]

    if posicion and posicion != ALL_TEXT:
        jugadoras_filtradas = jugadoras_filtradas[
            jugadoras_filtradas["posicion"] == posicion
        ]

    if not jugadoras_filtradas.empty and "id_jugadora" in records.columns:
        records_filtrados = records[
            records["id_jugadora"].isin(jugadoras_filtradas["id_jugadora"])
        ].copy()
    else:
        records_filtrados = records.iloc[0:0].copy()

    # --- FILTRO 3: Tipo de lesión ---
    with col3:
        tipos = sorted(records_filtrados["tipo_lesion"].dropna().unique().tolist()) if not records_filtrados.empty else []
        tipo_lesion = st.selectbox(
            t("Tipo de lesión"),
            [ALL_TEXT] + tipos,
            index=0
        )

        if tipo_lesion != ALL_TEXT:
            records_filtrados = records_filtrados[
                records_filtrados["tipo_lesion"] == tipo_lesion
            ]

    # --- Fechas disponibles tras filtros NO temporales ---
    if records_filtrados.empty:
        min_date_global = min_date_base
        max_date_global = max_date_base
    else:
        min_date_global = records_filtrados["fecha_lesion"].min().date()
        max_date_global = records_filtrados["fecha_lesion"].max().date()

    # Semana y mes anclados a última lesión
    fecha_ref_lesion = max_date_global if max_date_global else hoy

    # --- FILTRO 4: Rango rápido ---
    with col4:
        rango_rapido = st.selectbox(
            t("Rango rápido"),
            [
                t("Semana"),
                t("Mes"),
                t("Últimos 3 meses"),
                t("Últimos 6 meses"),
                t("Temporada"),
                t("Todo"),
                t("Personalizado"),
            ],
            index=1
        )

    # --- Resolver fechas según preset ---
    if rango_rapido == t("Semana"):
        ref = fecha_ref_lesion
        inicio_semana = ref - datetime.timedelta(days=ref.weekday())
        fin_semana = inicio_semana + datetime.timedelta(days=6)
        fecha_inicio = inicio_semana
        fecha_fin = min(fin_semana, ref)

    elif rango_rapido == t("Mes"):
        ref = fecha_ref_lesion
        fecha_inicio = ref.replace(day=1)
        fecha_fin = ref

    elif rango_rapido == t("Últimos 3 meses"):
        fecha_fin = fecha_ref_natural
        año = fecha_fin.year
        mes = fecha_fin.month - 2
        while mes <= 0:
            mes += 12
            año -= 1
        fecha_inicio = datetime.date(año, mes, 1)

    elif rango_rapido == t("Últimos 6 meses"):
        fecha_fin = fecha_ref_natural
        año = fecha_fin.year
        mes = fecha_fin.month - 5
        while mes <= 0:
            mes += 12
            año -= 1
        fecha_inicio = datetime.date(año, mes, 1)

    elif rango_rapido == t("Temporada"):
        fecha_inicio = inicio_temporada
        fecha_fin = fecha_ref_natural

    elif rango_rapido == t("Todo"):
        fecha_inicio = min_date_global
        fecha_fin = max_date_global

    else:  # Personalizado
        fecha_inicio = min_date_global
        fecha_fin = max_date_global

    # --- Ajuste de seguridad para el widget ---
    # El widget puede mostrar hasta hoy, pero no antes del mínimo histórico
    fecha_inicio = max(fecha_inicio, min_date_base)
    fecha_fin = min(fecha_fin, hoy)

    if fecha_inicio > fecha_fin:
        fecha_inicio = min_date_base
        fecha_fin = min(fecha_ref_lesion, hoy)

    # --- FILTRO 5: Rango visible ---
    with col5:
        if rango_rapido == t("Personalizado"):
            fecha_inicio, fecha_fin = st.date_input(
                t("Rango de fechas"),
                value=(fecha_inicio, fecha_fin),
                min_value=min_date_base,
                max_value=hoy,
                format="YYYY-MM-DD"
            )
        else:
            st.date_input(
                t("Rango de fechas"),
                value=(fecha_inicio, fecha_fin),
                min_value=min_date_base,
                max_value=hoy,
                format="YYYY-MM-DD",
                disabled=True
            )

    # --- Aplicar filtro de fechas ---
    if fecha_inicio and fecha_fin:
        mask = (
            (records_filtrados["fecha_lesion"] >= pd.to_datetime(fecha_inicio)) &
            (records_filtrados["fecha_lesion"] <= pd.to_datetime(fecha_fin))
        )
        records_periodo = records_filtrados.loc[mask].copy()
    else:
        records_periodo = records_filtrados.copy()

    # --- Mensajes informativos si no hay datos en el periodo ---
    if records_periodo.empty:
        if not records_filtrados.empty and max_date_global is not None:
            st.info(
                f"{t('Sin datos de lesiones para este periodo.')} "
                f"{t('Última lesión registrada')}: {max_date_global.strftime('%d/%m/%Y')}"
            )
        else:
            st.info(t("No hay lesiones registradas para los filtros seleccionados."))

    return competicion, posicion, tipo_lesion, rango_rapido, (fecha_inicio, fecha_fin), records_periodo, records_filtrados


def main_metrics(records, modo="overview"):
    """
    Métricas principales de lesiones.

    overview:
    - selector Semana / Mes / Temporada
    - Semana y Mes se calculan respecto a la última fecha disponible en los datos
      para evitar tarjetas vacías si el periodo natural actual no tiene lesiones.
    - Lesiones activas siempre se calculan sobre todo el dataset (estado actual)
    - Deltas absolutos (casos / días), no porcentuales

    reporte:
    - usa todo el dataframe sin selector ni comparativas
    """

    import pandas as pd
    import streamlit as st
    from modules.i18n.i18n import t

    # --------------------------------------------------
    # Validación inicial
    # --------------------------------------------------
    if records is None or records.empty:
        st.warning(t("No hay datos de lesiones disponibles."))
        st.stop()

    df = records.copy()

    if "fecha_lesion" not in df.columns:
        st.warning(t("No existe la columna fecha_lesion en los registros."))
        st.stop()

    df["fecha_lesion"] = pd.to_datetime(df["fecha_lesion"], errors="coerce")
    df = df.dropna(subset=["fecha_lesion"]).copy()

    if df.empty:
        st.warning(t("No hay fechas de lesión válidas para mostrar métricas."))
        st.stop()

    # Fecha de referencia para semana/mes:
    # usamos la última fecha con lesión registrada, no el día real de hoy
    fecha_ref = df["fecha_lesion"].max().normalize()

    # Fecha real para textos de activas si quieres mantener concepto “a día de hoy”
    hoy = pd.Timestamp.today().normalize()

    inicio_temporada = pd.Timestamp("2025-07-16")

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def safe_mean(series):
        s = pd.to_numeric(series, errors="coerce").dropna()
        return round(s.mean(), 1) if not s.empty else 0

    def fmt_delta_abs(valor, unidad_singular, unidad_plural=None):
        if valor is None or pd.isna(valor):
            return None

        if unidad_plural is None:
            unidad_plural = unidad_singular

        if isinstance(valor, float) and not float(valor).is_integer():
            valor_fmt = round(valor, 1)
        else:
            valor_fmt = int(valor)

        signo = "+" if valor_fmt > 0 else ""
        abs_val = abs(valor_fmt)
        unidad = unidad_singular if abs_val == 1 else unidad_plural
        return f"{signo}{valor_fmt} {unidad}"

    def count_active(df_in):
        if "estado_lesion" not in df_in.columns:
            return 0
        return int(df_in["estado_lesion"].fillna("").eq("ACTIVO").sum())

    def count_recidivas(df_in):
        if "es_recidiva" not in df_in.columns:
            return 0
        return int(df_in["es_recidiva"].fillna(False).astype(bool).sum())

    def top_label_and_count(df_in, col):
        if col not in df_in.columns:
            return "-", 0

        s = (
            df_in[col]
            .dropna()
            .astype(str)
            .str.strip()
        )
        s = s[s != ""]

        if s.empty:
            return "-", 0

        vc = s.value_counts()
        return vc.index[0], int(vc.iloc[0])

    def periodo_semana(df_in, ref_date):
        inicio_actual = ref_date - pd.Timedelta(days=ref_date.weekday())
        fin_actual = inicio_actual + pd.Timedelta(days=6)

        inicio_prev = inicio_actual - pd.Timedelta(days=7)
        fin_prev = inicio_actual - pd.Timedelta(days=1)

        actual = df_in[
            (df_in["fecha_lesion"] >= inicio_actual) &
            (df_in["fecha_lesion"] <= fin_actual)
        ].copy()

        previo = df_in[
            (df_in["fecha_lesion"] >= inicio_prev) &
            (df_in["fecha_lesion"] <= fin_prev)
        ].copy()

        return actual, previo, inicio_actual, fin_actual

    def periodo_mes(df_in, ref_date):
        inicio_actual = ref_date.replace(day=1)
        fin_actual = (inicio_actual + pd.offsets.MonthEnd(0)).normalize()

        fin_prev = inicio_actual - pd.Timedelta(days=1)
        inicio_prev = fin_prev.replace(day=1)

        actual = df_in[
            (df_in["fecha_lesion"] >= inicio_actual) &
            (df_in["fecha_lesion"] <= fin_actual)
        ].copy()

        previo = df_in[
            (df_in["fecha_lesion"] >= inicio_prev) &
            (df_in["fecha_lesion"] <= fin_prev)
        ].copy()

        return actual, previo, inicio_actual, fin_actual

    def periodo_temporada(df_in):
        actual = df_in[df_in["fecha_lesion"] >= inicio_temporada].copy()
        previo = pd.DataFrame(columns=df_in.columns)
        return actual, previo, inicio_temporada, fecha_ref

    def build_series_counts(df_in, freq="W"):
        if df_in.empty:
            return []

        temp = df_in.copy()

        if freq == "W":
            temp["bucket"] = temp["fecha_lesion"].dt.to_period("W").astype(str)
        else:
            temp["bucket"] = temp["fecha_lesion"].dt.to_period("M").astype(str)

        out = temp.groupby("bucket").size()
        return out.tolist()

    def build_series_avg_days(df_in, freq="W"):
        if df_in.empty or "dias_baja_estimado" not in df_in.columns:
            return []

        temp = df_in.copy()
        temp["dias_baja_estimado"] = pd.to_numeric(temp["dias_baja_estimado"], errors="coerce")

        if freq == "W":
            temp["bucket"] = temp["fecha_lesion"].dt.to_period("W").astype(str)
        else:
            temp["bucket"] = temp["fecha_lesion"].dt.to_period("M").astype(str)

        out = (
            temp.groupby("bucket")["dias_baja_estimado"]
            .mean()
            .round(1)
            .fillna(0)
        )
        return out.tolist()
    
    def pct_lesiones_graves(df_in):
        if df_in.empty or "impacto_dias_baja_estimado" not in df_in.columns:
            return 0.0, 0, 0

        total = len(df_in)
        if total == 0:
            return 0.0, 0, 0

        s = (
            df_in["impacto_dias_baja_estimado"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )

        graves = s.isin(["GRAVE", "MUY GRAVE"]).sum()
        pct = round((graves / total) * 100, 1) if total > 0 else 0.0
        return pct, int(graves), int(total)

    # --------------------------------------------------
    # Selector de periodo
    # --------------------------------------------------
    if modo == "overview":
        opciones = {
            "Semana": t("Semana"),
            "Mes": t("Mes"),
            "Temporada": t("Temporada"),
        }

        periodo_traducido = st.radio(
            t("Periodo:"),
            list(opciones.values()),
            horizontal=True,
            index=0
        )

        periodo = next(k for k, v in opciones.items() if v == periodo_traducido)

        if periodo == "Semana":
            df_periodo, df_prev, inicio_p, fin_p = periodo_semana(df, fecha_ref)
            subtitulo_periodo = f"{inicio_p.strftime('%d/%m/%Y')} - {fin_p.strftime('%d/%m/%Y')}"
            total_delta = len(df_periodo) - len(df_prev)
            recidivas_delta = count_recidivas(df_periodo) - count_recidivas(df_prev)
            dias_delta = round(
                safe_mean(df_periodo["dias_baja_estimado"]) - safe_mean(df_prev["dias_baja_estimado"]),
                1
            )
            chart_total = build_series_counts(df[df["fecha_lesion"] >= (inicio_p - pd.Timedelta(days=56))], "W")
            chart_dias = build_series_avg_days(df[df["fecha_lesion"] >= (inicio_p - pd.Timedelta(days=56))], "W")

        elif periodo == "Mes":
            df_periodo, df_prev, inicio_p, fin_p = periodo_mes(df, fecha_ref)
            subtitulo_periodo = inicio_p.strftime("%m/%Y")
            total_delta = len(df_periodo) - len(df_prev)
            recidivas_delta = count_recidivas(df_periodo) - count_recidivas(df_prev)
            dias_delta = round(
                safe_mean(df_periodo["dias_baja_estimado"]) - safe_mean(df_prev["dias_baja_estimado"]),
                1
            )
            chart_total = build_series_counts(df[df["fecha_lesion"] >= (inicio_p - pd.DateOffset(months=8))], "M")
            chart_dias = build_series_avg_days(df[df["fecha_lesion"] >= (inicio_p - pd.DateOffset(months=8))], "M")

        else:  # Temporada
            df_periodo, df_prev, inicio_p, fin_p = periodo_temporada(df)
            subtitulo_periodo = f"{inicio_temporada.strftime('%d/%m/%Y')} - {fecha_ref.strftime('%d/%m/%Y')}"
            total_delta = None
            recidivas_delta = None
            dias_delta = None
            chart_total = build_series_counts(df_periodo, "M")
            chart_dias = build_series_avg_days(df_periodo, "M")

    else:
        periodo = "Reporte"
        df_periodo = df.copy()
        df_prev = pd.DataFrame(columns=df.columns)
        subtitulo_periodo = t("Periodo completo")
        total_delta = None
        recidivas_delta = None
        dias_delta = None
        chart_total = build_series_counts(df_periodo, "M")
        chart_dias = build_series_avg_days(df_periodo, "M")

    # --------------------------------------------------
    # KPIs principales
    # --------------------------------------------------
    total_lesiones = len(df_periodo)
    lesiones_activas = count_active(df)  # siempre globales / actuales
    dias_promedio = safe_mean(df_periodo["dias_baja_estimado"]) if "dias_baja_estimado" in df_periodo.columns else 0
    recidivas = count_recidivas(df_periodo)

    zona_top, zona_count = top_label_and_count(df_periodo, "zona_cuerpo")
    tipo_top, tipo_count = top_label_and_count(df_periodo, "tipo_lesion")
    jugadora_top, jugadora_count = top_label_and_count(df_periodo, "nombre_jugadora")
    pct_graves, graves_count, graves_total = pct_lesiones_graves(df_periodo)

    total_delta_txt = fmt_delta_abs(total_delta, t("caso"), t("casos")) if total_delta is not None else None
    dias_delta_txt = fmt_delta_abs(dias_delta, t("día"), t("días")) if dias_delta is not None else None
    recidivas_delta_txt = fmt_delta_abs(recidivas_delta, t("caso"), t("casos")) if recidivas_delta is not None else None

    casos_zona = t("caso") if zona_count == 1 else t("casos")
    casos_tipo = t("caso") if tipo_count == 1 else t("casos")
    casos_jug = t("caso") if jugadora_count == 1 else t("casos")

    
    if modo == "overview":
    # bloque actual de inicio

        # --------------------------------------------------
        # FILA 1
        # --------------------------------------------------
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                t("Total de lesiones registradas"),
                total_lesiones,
                total_delta_txt,
                chart_data=chart_total if chart_total else None,
                chart_type="area" if chart_total else None,
                border=True,
                delta_color="inverse",
                help=f"{t('Lesiones producidas en el periodo seleccionado')}. {subtitulo_periodo}"
            )

        with col2:
            st.metric(
                t("Lesiones activas"),
                lesiones_activas,
                None,
                border=True,
                delta_color="inverse",
                help=f"{t('Lesiones activas actualmente, independientemente del periodo seleccionado')}. {hoy.strftime('%d/%m/%Y')}"
            )

        with col3:
            st.metric(
                t("Días de recuperación promedio"),
                dias_promedio,
                dias_delta_txt,
                chart_data=chart_dias if chart_dias else None,
                chart_type="area" if chart_dias else None,
                border=True,
                delta_color="inverse",
                help=f"{t('Promedio de días de baja estimados en el periodo seleccionado')}. {subtitulo_periodo}"
            )

        with col4:
            st.metric(
                t("Recidivas"),
                recidivas,
                recidivas_delta_txt,
                border=True,
                delta_color="inverse",
                help=f"{t('Número de lesiones marcadas como recidiva en el periodo seleccionado')}. {subtitulo_periodo}"
            )

        # --------------------------------------------------
        # FILA 2
        # --------------------------------------------------
        col5, col6, col7, col8 = st.columns(4)

        with col5:
            st.metric(
                t("% lesiones graves/muy graves"),
                f"{pct_graves:.1f}%",
                None,
                border=True,
                delta_color="inverse",
                help=f"{graves_count} de {graves_total} lesiones del periodo clasificadas como graves o muy graves."
            )

        with col6:
            st.metric(
                t("Zona más afectada"),
                zona_top,
                f"{zona_count} {casos_zona}",
                border=True,
                delta_color="off",
                help=t("Zona corporal con mayor número de lesiones en el periodo seleccionado.")
            )

        with col7:
            st.metric(
                t("Tipo más frecuente"),
                tipo_top,
                f"{tipo_count} {casos_tipo}",
                border=True,
                delta_color="off",
                help=t("Tipo de lesión más repetido en el periodo seleccionado.")
            )

        with col8:
            st.metric(
                t("Jugadora con más lesiones"),
                jugadora_top,
                f"{jugadora_count} {casos_jug}",
                border=True,
                delta_color="off",
                help=t("Jugadora con mayor número de lesiones registradas en el periodo seleccionado.")
            )

    else:
        # --------------------------------------------------
        # KPIs para reporte / individual
        # --------------------------------------------------
        dias_totales = (
            pd.to_numeric(df_periodo["dias_baja_estimado"], errors="coerce").fillna(0).sum().round(1)
            if "dias_baja_estimado" in df_periodo.columns else 0
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                t("Total de lesiones registradas"),
                total_lesiones,
                border=True,
                help=t("Número total de lesiones registradas .")
            )

        with col2:
            st.metric(
                t("Lesiones activas"),
                lesiones_activas,
                None,
                border=True,
                help=t("Número actual de lesiones activas.")
            )

        with col3:
            st.metric(
                t("Días de baja totales"),
                dias_totales,
                border=True,
                help=t("Suma de los días estimados de baja.")
            )

        with col4:
            st.metric(
                t("Recidivas"),
                recidivas,
                border=True,
                help=t("Número de lesiones marcadas como recidiva.")
            )

        col5, col6, col7, col8 = st.columns(4)

        with col5:
            st.metric(
                t("Días de baja promedio"),
                dias_promedio,
                border=True,
                help=t("Promedio de días estimados de baja por lesión.")
            )

        with col6:
            st.metric(
                t("% lesiones graves/muy graves"),
                f"{pct_graves:.1f}%",
                border=True,
                help=f"{graves_count} de {graves_total} lesiones clasificadas como graves o muy graves."
            )
            st.caption(f"{graves_count} {t('de')} {graves_total}")

        with col7:
            st.metric(
                t("Zona más afectada"),
                zona_top,
                f"{zona_count} {casos_zona}",
                border=True,
                delta_color="off",
                help=t("Zona corporal con mayor número de lesiones.")
            )

        with col8:
            st.metric(
                t("Tipo más frecuente"),
                tipo_top,
                f"{tipo_count} {casos_tipo}",
                border=True,
                delta_color="off",
                help=t("Tipo de lesión más repetido.")
            )

    return df_periodo.sort_values("fecha_lesion", ascending=False)


def latest_lesiones_panel(df_resumen):
    """
    Panel de últimas lesiones con:
    - filtros
    - tabla interactiva
    - selector para abrir análisis individual
    """

    import pandas as pd
    import streamlit as st
    from modules.i18n.i18n import t

    if df_resumen is None or df_resumen.empty:
        st.info(t("No hay lesiones para mostrar en el periodo seleccionado."))
        return pd.DataFrame()

    df = df_resumen.copy()

    # -----------------------------
    # Normalización básica
    # -----------------------------
    if "fecha_lesion" in df.columns:
        df["fecha_lesion"] = pd.to_datetime(df["fecha_lesion"], errors="coerce")

    # -----------------------------
    # Filtros
    # -----------------------------
    col1, col2, col3 = st.columns([2, 1.2, 1.2])

    with col1:
        opciones_jugadora = ["Todas"] + sorted(df["nombre_jugadora"].dropna().astype(str).unique().tolist()) \
            if "nombre_jugadora" in df.columns else ["Todas"]

        filtro_jugadora = st.selectbox(
            t("Filtrar por jugadora"),
            opciones_jugadora,
            index=0,
            key="home_filtro_jugadora"
        )

    with col2:
        opciones_tipo = ["Todos"] + sorted(df["tipo_lesion"].dropna().astype(str).unique().tolist()) \
            if "tipo_lesion" in df.columns else ["Todos"]

        filtro_tipo = st.selectbox(
            t("Tipo de lesión"),
            opciones_tipo,
            index=0,
            key="home_filtro_tipo"
        )

    with col3:
        opciones_estado = ["Todos"] + sorted(df["estado_lesion"].dropna().astype(str).str.strip().unique().tolist()) \
            if "estado_lesion" in df.columns else ["Todos"]

        filtro_estado = st.selectbox(
            t("Estado"),
            opciones_estado,
            index=0,
            key="home_filtro_estado"
        )

    # -----------------------------
    # Aplicar filtros
    # -----------------------------
    df_filtrado = df.copy()

    if filtro_jugadora != "Todas" and "nombre_jugadora" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["nombre_jugadora"] == filtro_jugadora]

    if filtro_tipo != "Todos" and "tipo_lesion" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["tipo_lesion"] == filtro_tipo]

    if filtro_estado != "Todos" and "estado_lesion" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["estado_lesion"] == filtro_estado]

    # -----------------------------
    # Orden y columnas
    # -----------------------------
    if "fecha_lesion" in df_filtrado.columns:
        df_filtrado = df_filtrado.sort_values("fecha_lesion", ascending=False)

        columnas_mostrar = [
        c for c in [
            "nombre_jugadora",
            "id_lesion",
            "fecha_lesion",
            "zona_cuerpo",
            "zona_especifica",
            "tipo_lesion",
            "dias_baja_estimado",
            "impacto_dias_baja_estimado",
            "estado_lesion",
            "personal_reporta",
        ]
        if c in df_filtrado.columns
    ]

        df_tabla = df_filtrado[columnas_mostrar].copy()
        

        if "fecha_lesion" in df_tabla.columns:
            df_tabla["fecha_lesion"] = pd.to_datetime(df_tabla["fecha_lesion"], errors="coerce").dt.strftime("%Y-%m-%d")

        df_tabla = df_tabla.rename(columns={
            "nombre_jugadora": t("Jugadora"),
            "id_lesion": t("ID lesión"),
            "fecha_lesion": t("Fecha lesión"),
            "zona_cuerpo": t("Zona"),
            "zona_especifica": t("Zona específica"),
            "tipo_lesion": t("Tipo lesión"),
            "dias_baja_estimado": t("Días baja"),
            "impacto_dias_baja_estimado": t("Gravedad"),
            "estado_lesion": t("Estado"),
            "personal_reporta": t("Reporta"),
        })

    # -----------------------------
    # Tabla interactiva
    # -----------------------------
    event = st.dataframe(
        df_tabla,
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="home_tabla_lesiones"
    )

    selected_rows = event.selection.rows if event and event.selection else []

    # -----------------------------
    # Selector para ir a individual
    # -----------------------------
    st.markdown("")
    opciones_abrir = sorted(df_filtrado["nombre_jugadora"].dropna().astype(str).unique().tolist()) \
        if "nombre_jugadora" in df_filtrado.columns else []

    jugadora_ir = st.selectbox(
        t("Abrir análisis individual de"),
        opciones_abrir,
        index=0 if opciones_abrir else None,
        placeholder=t("Seleccione una jugadora"),
        key="home_ir_individual"
    )

    col_btn1, col_btn2 = st.columns([1.2, 5])

    with col_btn1:
        if st.button(t("Abrir análisis"), use_container_width=True, disabled=not jugadora_ir):
            st.session_state["jugadora_nombre"] = jugadora_ir
            st.switch_page("pages/individual.py")

    # -----------------------------
    # Si selecciona fila, preseleccionar jugadora
    # -----------------------------
    if selected_rows:
        row_index = selected_rows[0]
        jugadora_fila = df_tabla.iloc[row_index]["nombre_jugadora"]

        st.info(f"{t('Lesión seleccionada de')}: **{jugadora_fila}**")

        col_a, col_b = st.columns([1.2, 5])

        with col_a:
            if st.button(t("Ir a su análisis"), use_container_width=True, key="home_ir_fila"):
                st.session_state["jugadora_nombre"] = jugadora_fila
                st.switch_page("pages/individual.py")

    return df_filtrado
