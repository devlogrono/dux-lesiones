import streamlit as st
from modules.i18n.i18n import t

import streamlit as st
import pandas as pd
from modules.i18n.i18n import t


def groupal_metrics(
    df_filtrado: pd.DataFrame,
    records_base: pd.DataFrame,
    rango_rapido: str | None = None,
    fechas: tuple | None = None,
):
    """
    KPIs grupales de lesiones con help y deltas inteligentes.

    df_filtrado:
        dataframe ya filtrado por plantel/posición/tipo/fechas (periodo actual)

    records_base:
        dataframe base sin filtro temporal final, pero sí con el mismo universo general
        de datos de lesiones para poder calcular el periodo comparativo

    rango_rapido:
        Semana / Mes / Últimos 3 meses / Últimos 6 meses / Temporada / Todo / Personalizado

    fechas:
        (fecha_inicio, fecha_fin) del periodo actual
    """

    if df_filtrado is None or df_filtrado.empty:
        st.info(t("No hay datos para mostrar KPIs grupales."))
        return

    df = df_filtrado.copy()
    base = records_base.copy() if records_base is not None else df.copy()

    df["fecha_lesion"] = pd.to_datetime(df["fecha_lesion"], errors="coerce")
    base["fecha_lesion"] = pd.to_datetime(base["fecha_lesion"], errors="coerce")

    df = df.dropna(subset=["fecha_lesion"]).copy()
    base = base.dropna(subset=["fecha_lesion"]).copy()

    if df.empty or base.empty:
        st.info(t("No hay datos válidos para mostrar KPIs grupales."))
        return

    # --------------------------------------------------
    # Helpers
    # --------------------------------------------------
    def get_bucket_freq(rango_label: str | None, fechas: tuple | None = None) -> str:
        if fechas and fechas[0] and fechas[1]:
            fecha_inicio = pd.to_datetime(fechas[0])
            fecha_fin = pd.to_datetime(fechas[1])
            duracion = (fecha_fin - fecha_inicio).days + 1

            if duracion <= 7:
                return "D"
            if duracion <= 31:
                return "W"
            return "M"

        if rango_label == t("Semana"):
            return "D"
        if rango_label == t("Mes"):
            return "W"
        return "M"


    def build_metric_series(df_in: pd.DataFrame, value_type: str, freq: str = "M") -> list:
        if df_in is None or df_in.empty or "fecha_lesion" not in df_in.columns:
            return []

        temp = df_in.copy()
        temp["fecha_lesion"] = pd.to_datetime(temp["fecha_lesion"], errors="coerce")
        temp = temp.dropna(subset=["fecha_lesion"]).copy()

        if temp.empty:
            return []

        if freq == "D":
            temp["bucket"] = temp["fecha_lesion"].dt.strftime("%Y-%m-%d")
        elif freq == "W":
            temp["bucket"] = temp["fecha_lesion"].dt.to_period("W").astype(str)
        else:
            temp["bucket"] = temp["fecha_lesion"].dt.to_period("M").astype(str)

        if value_type == "total_lesiones":
            serie = temp.groupby("bucket").size()

        elif value_type == "jugadoras_lesionadas":
            col_player = "id_jugadora" if "id_jugadora" in temp.columns else "nombre_jugadora"
            if col_player not in temp.columns:
                return []
            serie = temp.groupby("bucket")[col_player].nunique()

        elif value_type == "recidivas":
            if "es_recidiva" not in temp.columns:
                return []
            temp["es_recidiva"] = temp["es_recidiva"].fillna(False).astype(bool)
            serie = temp.groupby("bucket")["es_recidiva"].sum()

        elif value_type == "dias_baja_totales":
            if "dias_baja_estimado" not in temp.columns:
                return []
            temp["dias_baja_estimado"] = pd.to_numeric(temp["dias_baja_estimado"], errors="coerce").fillna(0)
            serie = temp.groupby("bucket")["dias_baja_estimado"].sum().round(1)

        elif value_type == "dias_baja_promedio":
            if "dias_baja_estimado" not in temp.columns:
                return []
            temp["dias_baja_estimado"] = pd.to_numeric(temp["dias_baja_estimado"], errors="coerce")
            serie = temp.groupby("bucket")["dias_baja_estimado"].mean().fillna(0).round(1)

        elif value_type == "pct_lesiones_graves":
            if "impacto_dias_baja_estimado" not in temp.columns:
                return []
            temp["grave_flag"] = (
                temp["impacto_dias_baja_estimado"]
                .fillna("")
                .astype(str)
                .str.strip()
                .str.upper()
                .eq("GRAVE")
                .astype(int)
            )
            grp = temp.groupby("bucket").agg(total=("grave_flag", "size"), graves=("grave_flag", "sum"))
            serie = ((grp["graves"] / grp["total"]) * 100).fillna(0).round(1)

        elif value_type == "pct_lesiones_con_baja":
            if "dias_baja_estimado" not in temp.columns:
                return []
            temp["con_baja_flag"] = pd.to_numeric(temp["dias_baja_estimado"], errors="coerce").fillna(0).gt(0).astype(int)
            grp = temp.groupby("bucket").agg(total=("con_baja_flag", "size"), con_baja=("con_baja_flag", "sum"))
            serie = ((grp["con_baja"] / grp["total"]) * 100).fillna(0).round(1)

        else:
            return []

        return serie.tolist()

    def safe_top(df_in: pd.DataFrame, col: str):
        if col not in df_in.columns:
            return "N/A", 0
        s = df_in[col].dropna().astype(str).str.strip()
        s = s[s != ""]
        if s.empty:
            return "N/A", 0
        vc = s.value_counts()
        return vc.index[0], int(vc.iloc[0])

    def safe_mean(series):
        s = pd.to_numeric(series, errors="coerce").dropna()
        return round(s.mean(), 1) if not s.empty else 0

    def safe_sum(series):
        s = pd.to_numeric(series, errors="coerce").dropna()
        return round(s.sum(), 1) if not s.empty else 0

    def count_players(df_in: pd.DataFrame):
        if "id_jugadora" in df_in.columns:
            return int(df_in["id_jugadora"].astype(str).nunique())
        if "nombre_jugadora" in df_in.columns:
            return int(df_in["nombre_jugadora"].astype(str).nunique())
        return 0

    def count_active(df_in: pd.DataFrame):
        if "estado_lesion" not in df_in.columns:
            return 0
        return int(df_in["estado_lesion"].fillna("").eq("ACTIVO").sum())

    def count_recidivas(df_in: pd.DataFrame):
        if "es_recidiva" not in df_in.columns:
            return 0
        return int(df_in["es_recidiva"].fillna(False).astype(bool).sum())

    def count_with_baja(df_in: pd.DataFrame):
        if "dias_baja_estimado" not in df_in.columns:
            return 0
        s = pd.to_numeric(df_in["dias_baja_estimado"], errors="coerce").fillna(0)
        return int(s.gt(0).sum())

    def count_graves(df_in: pd.DataFrame):
        if "impacto_dias_baja_estimado" not in df_in.columns:
            return 0
        s = (
            df_in["impacto_dias_baja_estimado"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
        )
        return int(s.eq("GRAVE").sum())

    def pct(part, total):
        return round((part / total) * 100, 1) if total > 0 else 0

    def fmt_delta_cases(value):
        if value is None:
            return None
        n = int(round(value))
        signo = "+" if n > 0 else ""
        unidad = t("caso") if abs(n) == 1 else t("casos")
        return f"{signo}{n} {unidad}"

    def fmt_delta_days(value):
        if value is None:
            return None
        n = round(value, 1)
        signo = "+" if n > 0 else ""
        unidad = t("día") if abs(n) == 1 else t("días")
        return f"{signo}{n} {unidad}"

    def fmt_delta_pp(value):
        if value is None:
            return None
        n = round(value, 1)
        signo = "+" if n > 0 else ""
        return f"{signo}{n} pp"

    def get_previous_period(fecha_inicio, fecha_fin, rango_label):
        if fecha_inicio is None or fecha_fin is None:
            return None, None

        inicio = pd.to_datetime(fecha_inicio).normalize()
        fin = pd.to_datetime(fecha_fin).normalize()

        if rango_label == t("Semana"):
            prev_inicio = inicio - pd.Timedelta(days=7)
            prev_fin = fin - pd.Timedelta(days=7)
            return prev_inicio, prev_fin

        if rango_label == t("Mes"):
            # Mes natural anterior completo/equivalente hasta el mismo día si aplica
            prev_fin = inicio - pd.Timedelta(days=1)
            prev_inicio = prev_fin.replace(day=1)
            return prev_inicio, prev_fin

        if rango_label == t("Últimos 3 meses"):
            # Ejemplo actual: 01/02 - 21/04
            # previo: 01/11 - 21/01
            dia_fin = fin.day

            año_fin_prev = inicio.year
            mes_fin_prev = inicio.month - 1
            if mes_fin_prev <= 0:
                mes_fin_prev += 12
                año_fin_prev -= 1

            # fin del periodo previo: mismo día del mes que el fin actual, pero en el mes anterior al inicio actual
            # si ese mes no tiene ese día, usa el último día disponible
            ultimo_dia_mes_prev = (
                pd.Timestamp(año_fin_prev, mes_fin_prev, 1) + pd.offsets.MonthEnd(0)
            ).day
            dia_fin_ajustado = min(dia_fin, ultimo_dia_mes_prev)

            prev_fin = pd.Timestamp(año_fin_prev, mes_fin_prev, dia_fin_ajustado).normalize()

            # inicio: primer día de dos meses antes de prev_fin (para cubrir 3 meses en total)
            año_inicio_prev = prev_fin.year
            mes_inicio_prev = prev_fin.month - 2
            while mes_inicio_prev <= 0:
                mes_inicio_prev += 12
                año_inicio_prev -= 1

            prev_inicio = pd.Timestamp(año_inicio_prev, mes_inicio_prev, 1).normalize()
            return prev_inicio, prev_fin

        if rango_label == t("Últimos 6 meses"):
            # Ejemplo actual: 01/11 - 21/04
            # previo: 01/05 - 21/10
            dia_fin = fin.day

            año_fin_prev = inicio.year
            mes_fin_prev = inicio.month - 1
            if mes_fin_prev <= 0:
                mes_fin_prev += 12
                año_fin_prev -= 1

            ultimo_dia_mes_prev = (
                pd.Timestamp(año_fin_prev, mes_fin_prev, 1) + pd.offsets.MonthEnd(0)
            ).day
            dia_fin_ajustado = min(dia_fin, ultimo_dia_mes_prev)

            prev_fin = pd.Timestamp(año_fin_prev, mes_fin_prev, dia_fin_ajustado).normalize()

            # inicio: primer día de cinco meses antes de prev_fin (para cubrir 6 meses en total)
            año_inicio_prev = prev_fin.year
            mes_inicio_prev = prev_fin.month - 5
            while mes_inicio_prev <= 0:
                mes_inicio_prev += 12
                año_inicio_prev -= 1

            prev_inicio = pd.Timestamp(año_inicio_prev, mes_inicio_prev, 1).normalize()
            return prev_inicio, prev_fin

        return None, None

    # --------------------------------------------------
    # Datos periodo actual
    # --------------------------------------------------
    total_lesiones = len(df)
    jugadoras_lesionadas = count_players(df)
    lesiones_activas = count_active(base)
    recidivas = count_recidivas(df)

    dias_baja_totales = safe_sum(df["dias_baja_estimado"]) if "dias_baja_estimado" in df.columns else 0
    dias_baja_promedio = safe_mean(df["dias_baja_estimado"]) if "dias_baja_estimado" in df.columns else 0

    lesiones_con_baja = count_with_baja(df)
    pct_lesiones_con_baja = pct(lesiones_con_baja, total_lesiones)

    lesiones_graves = count_graves(df)
    pct_lesiones_graves = pct(lesiones_graves, total_lesiones)

    tipo_top, tipo_count = safe_top(df, "tipo_lesion")
    zona_top, zona_count = safe_top(df, "zona_cuerpo")
    mecanismo_top, mecanismo_count = safe_top(df, "mecanismo")
    lugar_top, lugar_count = safe_top(df, "lugar")

    # --------------------------------------------------
    # Datos periodo previo comparable
    # --------------------------------------------------
    fecha_inicio = fechas[0] if fechas else None
    fecha_fin = fechas[1] if fechas else None

    compara = rango_rapido in {
        t("Semana"),
        t("Mes"),
        t("Últimos 3 meses"),
        t("Últimos 6 meses"),
    }

    prev_inicio, prev_fin = get_previous_period(fecha_inicio, fecha_fin, rango_rapido) if compara else (None, None)

    if prev_inicio is not None and prev_fin is not None:
        df_prev = base[
            (base["fecha_lesion"] >= prev_inicio) &
            (base["fecha_lesion"] <= prev_fin)
        ].copy()
    else:
        df_prev = pd.DataFrame(columns=base.columns)

    if compara and not df_prev.empty:
        total_prev = len(df_prev)
        jugadoras_prev = count_players(df_prev)
        activas_prev = count_active(df_prev)
        recidivas_prev = count_recidivas(df_prev)
        dias_totales_prev = safe_sum(df_prev["dias_baja_estimado"]) if "dias_baja_estimado" in df_prev.columns else 0
        dias_prom_prev = safe_mean(df_prev["dias_baja_estimado"]) if "dias_baja_estimado" in df_prev.columns else 0
        con_baja_prev = count_with_baja(df_prev)
        graves_prev = count_graves(df_prev)

        pct_baja_prev = pct(con_baja_prev, total_prev)
        pct_graves_prev = pct(graves_prev, total_prev)

        delta_total = fmt_delta_cases(total_lesiones - total_prev)
        delta_jugadoras = fmt_delta_cases(jugadoras_lesionadas - jugadoras_prev)
        delta_activas = fmt_delta_cases(lesiones_activas - activas_prev)
        delta_recidivas = fmt_delta_cases(recidivas - recidivas_prev)

        delta_dias_totales = fmt_delta_days(dias_baja_totales - dias_totales_prev)
        delta_dias_prom = fmt_delta_days(dias_baja_promedio - dias_prom_prev)
        delta_pct_graves = fmt_delta_pp(pct_lesiones_graves - pct_graves_prev)
        delta_pct_baja = fmt_delta_pp(pct_lesiones_con_baja - pct_baja_prev)
    else:
        delta_total = None
        delta_jugadoras = None
        delta_activas = None
        delta_recidivas = None
        delta_dias_totales = None
        delta_dias_prom = None
        delta_pct_graves = None
        delta_pct_baja = None

    caso_txt = t("caso")
    casos_txt = t("casos")

    bucket_freq = get_bucket_freq(rango_rapido, fechas)

    chart_total = build_metric_series(base, "total_lesiones", bucket_freq)
    chart_jugadoras = build_metric_series(base, "jugadoras_lesionadas", bucket_freq)
    chart_recidivas = build_metric_series(base, "recidivas", bucket_freq)
    chart_dias_totales = build_metric_series(base, "dias_baja_totales", bucket_freq)
    chart_dias_prom = build_metric_series(base, "dias_baja_promedio", bucket_freq)
    chart_pct_graves = build_metric_series(base, "pct_lesiones_graves", bucket_freq)
    chart_pct_baja = build_metric_series(base, "pct_lesiones_con_baja", bucket_freq)

    # --------------------------------------------------
    # FILA 1
    # --------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            t("Total de lesiones"),
            total_lesiones,
            delta_total,
            chart_data=chart_total if chart_total else None,
            chart_type="area" if chart_total else None,
            border=True,
            delta_color="inverse",
            help=t("Número de lesiones registradas en el periodo seleccionado.")
        )

    with col2:
        st.metric(
            t("Jugadoras lesionadas"),
            jugadoras_lesionadas,
            delta_jugadoras,
            chart_data=chart_jugadoras if chart_jugadoras else None,
            chart_type="area" if chart_jugadoras else None,
            border=True,
            delta_color="inverse",
            help=t("Número de jugadoras distintas con al menos una lesión registrada en el periodo.")
        )

    with col3:
        st.metric(
            t("Lesiones activas"),
            lesiones_activas,
            # delta_activas,
            border=True,
            delta_color="inverse",
            help=t("Número de lesiones en estado activo dentro del conjunto filtrado.")
        )

    with col4:
        st.metric(
            t("Recidivas"),
            recidivas,
            delta_recidivas,
            chart_data=chart_recidivas if chart_recidivas else None,
            chart_type="area" if chart_recidivas else None,
            border=True,
            delta_color="inverse",
            help=t("Lesiones registradas en el periodo marcadas como recidiva.")
        )
        st.caption(f"{pct(recidivas, total_lesiones):.1f}%")

    # --------------------------------------------------
    # FILA 2
    # --------------------------------------------------
    col5, col6, col7, col8 = st.columns(4)

    with col5:
        st.metric(
            t("Días de baja totales"),
            dias_baja_totales,
            delta_dias_totales,
            chart_data=chart_dias_totales if chart_dias_totales else None,
            chart_type="area" if chart_dias_totales else None,
            border=True,
            delta_color="inverse",
            help=t("Suma de los días estimados de baja de todas las lesiones del periodo.")
        )

    with col6:
        st.metric(
            t("Días de baja promedio"),
            dias_baja_promedio,
            delta_dias_prom,
            chart_data=chart_dias_prom if chart_dias_prom else None,
            chart_type="area" if chart_dias_prom else None,
            border=True,
            delta_color="inverse",
            help=t("Promedio de días estimados de baja por lesión en el periodo.")
        )

    with col7:
        st.metric(
            t("% lesiones graves/muy graves"),
            f"{pct_lesiones_graves:.1f}%",
            delta_pct_graves,
            chart_data=chart_pct_graves if chart_pct_graves else None,
            chart_type="area" if chart_pct_graves else None,
            border=True,
            delta_color="inverse",
            help=t("Porcentaje de lesiones del periodo clasificadas como graves o muy graves.")
        )
        st.caption(f"{lesiones_graves} {t('de')} {total_lesiones}")

    with col8:
        st.metric(
            t("% lesiones con baja"),
            f"{pct_lesiones_con_baja:.1f}%",
            delta_pct_baja,
            chart_data=chart_pct_baja if chart_pct_baja else None,
            chart_type="area" if chart_pct_baja else None,
            border=True,
            delta_color="inverse",
            help=t("Porcentaje de lesiones del periodo con días estimados de baja mayores que cero.")
        )
        st.caption(f"{lesiones_con_baja} {t('de')} {total_lesiones}")

    # --------------------------------------------------
    # FILA 3
    # --------------------------------------------------
    col9, col10, col11, col12 = st.columns(4)

    with col9:
        st.metric(
            t("Tipo más frecuente"),
            tipo_top,
            f"{tipo_count} {caso_txt if tipo_count == 1 else casos_txt}",
            delta_color="off",
            border=True,
            help=t("Tipo de lesión más repetido en el periodo seleccionado.")
        )

    with col10:
        st.metric(
            t("Zona más afectada"),
            zona_top,
            f"{zona_count} {caso_txt if zona_count == 1 else casos_txt}",
            delta_color="off",
            border=True,
            help=t("Zona corporal con mayor número de lesiones en el periodo.")
        )

    with col11:
        st.metric(
            t("Mecanismo más frecuente"),
            mecanismo_top,
            f"{mecanismo_count} {caso_txt if mecanismo_count == 1 else casos_txt}",
            delta_color="off",
            border=True,
            help=t("Mecanismo de lesión más repetido en el periodo.")
        )

    with col12:
        st.metric(
            t("Lugar más frecuente"),
            lugar_top,
            f"{lugar_count} {caso_txt if lugar_count == 1 else casos_txt}",
            delta_color="off",
            border=True,
            help=t("Lugar donde más lesiones se registraron en el periodo.")
        )

import pandas as pd
import plotly.express as px
from modules.i18n.i18n import t


def _get_time_bucket_config(rango_rapido: str | None, fechas: tuple | None = None):
    if fechas and fechas[0] and fechas[1]:
        fecha_inicio = pd.to_datetime(fechas[0])
        fecha_fin = pd.to_datetime(fechas[1])
        duracion = (fecha_fin - fecha_inicio).days + 1

        if duracion <= 7:
            return "D", t("Día"), "%d/%m"
        if duracion <= 31:
            return "SEMANA_MES", t("Semana del mes"), None
        return "MS", t("Mes"), "%b %Y"

    if rango_rapido == t("Semana"):
        return "D", t("Día"), "%d/%m"
    if rango_rapido == t("Mes"):
        return "SEMANA_MES", t("Semana del mes"), None
    return "MS", t("Mes"), "%b %Y"

def _label_semana_mes(semana: int, ultimo_dia_mes: int) -> str:
    inicio = (semana - 1) * 7 + 1
    fin = min(semana * 7, ultimo_dia_mes)
    return f"S{semana} ({inicio}–{fin})"

def _build_full_period_index(start, end, freq: str):
    start = pd.to_datetime(start)
    end = pd.to_datetime(end)

    if freq == "D":
        return pd.date_range(start=start.normalize(), end=end.normalize(), freq="D")

    if freq == "SEMANA_MES":
        max_semana = ((end.day - 1) // 7) + 1
        return list(range(1, max_semana + 1))

    # MS
    start_bucket = start.replace(day=1)
    end_bucket = end.replace(day=1)
    return pd.date_range(start=start_bucket.normalize(), end=end_bucket.normalize(), freq="MS")


def _aggregate_time_series(
    df: pd.DataFrame,
    value_col: str | None,
    agg: str,
    rango_rapido: str | None,
    fechas: tuple | None = None
):
    if df is None or df.empty or "fecha_lesion" not in df.columns:
        return None, None, None

    data = df.copy()
    data["fecha_lesion"] = pd.to_datetime(data["fecha_lesion"], errors="coerce")
    data = data.dropna(subset=["fecha_lesion"]).copy()

    if data.empty:
        return None, None, None

    freq, x_title, tickformat = _get_time_bucket_config(rango_rapido, fechas)

    start = data["fecha_lesion"].min()
    end = data["fecha_lesion"].max()

    if value_col is not None and value_col in data.columns and agg in ("sum", "mean"):
        data[value_col] = pd.to_numeric(data[value_col], errors="coerce")

    if freq == "D":
        if agg == "count":
            serie = data.groupby(pd.Grouper(key="fecha_lesion", freq="D")).size().rename("value")
        elif agg == "sum":
            serie = data.groupby(pd.Grouper(key="fecha_lesion", freq="D"))[value_col].sum(min_count=1).rename("value")
        elif agg == "mean":
            serie = data.groupby(pd.Grouper(key="fecha_lesion", freq="D"))[value_col].mean().rename("value")
        else:
            return None, None, None

        full_index = _build_full_period_index(start, end, freq)
        serie = serie.reindex(full_index, fill_value=0).reset_index()
        serie.columns = ["fecha_lesion", "value"]
        return serie, x_title, tickformat

    if freq == "SEMANA_MES":
        data["semana_mes"] = ((data["fecha_lesion"].dt.day - 1) // 7) + 1

        if agg == "count":
            serie = data.groupby("semana_mes").size().rename("value")
        elif agg == "sum":
            serie = data.groupby("semana_mes")[value_col].sum(min_count=1).rename("value")
        elif agg == "mean":
            serie = data.groupby("semana_mes")[value_col].mean().rename("value")
        else:
            return None, None, None

        full_index = _build_full_period_index(start, end, freq)
        serie = serie.reindex(full_index, fill_value=0).reset_index()
        serie.columns = ["semana_mes", "value"]
        ultimo_dia_mes = pd.to_datetime(end).day
        serie["label_x"] = serie["semana_mes"].apply(lambda x: _label_semana_mes(x, ultimo_dia_mes))
        return serie, x_title, tickformat

    # MS
    if agg == "count":
        serie = data.groupby(pd.Grouper(key="fecha_lesion", freq="MS")).size().rename("value")
    elif agg == "sum":
        serie = data.groupby(pd.Grouper(key="fecha_lesion", freq="MS"))[value_col].sum(min_count=1).rename("value")
    elif agg == "mean":
        serie = data.groupby(pd.Grouper(key="fecha_lesion", freq="MS"))[value_col].mean().rename("value")
    else:
        return None, None, None

    full_index = _build_full_period_index(start, end, freq)
    serie = serie.reindex(full_index, fill_value=0).reset_index()
    serie.columns = ["fecha_lesion", "value"]

    return serie, x_title, tickformat

def grafico_evolucion_dias_baja(df: pd.DataFrame, rango_rapido: str | None = None, fechas: tuple | None = None):
    serie, x_title, tickformat = _aggregate_time_series(df, "dias_baja_estimado", "sum", rango_rapido, fechas)
    if serie is None:
        return None

    serie["value"] = serie["value"].fillna(0).round(1)
    serie["label"] = serie["value"].apply(lambda x: f"{x:g}" if x > 0 else "")

    x_col = "label_x" if "label_x" in serie.columns else "fecha_lesion"

    fig = px.bar(
        serie,
        x=x_col,
        y="value",
        text="label",
        title=t("Evolución de días de baja estimados")
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        template="simple_white",
        height=420,
        xaxis_title=x_title,
        yaxis_title=t("Días de baja"),
        hovermode="x unified"
    )

    if x_col == "fecha_lesion":
        if _get_time_bucket_config(rango_rapido, fechas)[0] == "MS":
            fig.update_xaxes(tickformat="%b %Y", dtick="M1")
        else:
            fig.update_xaxes(tickformat=tickformat)

    return fig


def grafico_evolucion_nuevas_vs_recidivas(
    df: pd.DataFrame,
    rango_rapido: str | None = None,
    fechas: tuple | None = None
):
    if df is None or df.empty or "fecha_lesion" not in df.columns or "es_recidiva" not in df.columns:
        return None

    data = df.copy()
    data["fecha_lesion"] = pd.to_datetime(data["fecha_lesion"], errors="coerce")
    data = data.dropna(subset=["fecha_lesion"]).copy()

    data["es_recidiva_bool"] = (
        data["es_recidiva"]
        .fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "si", "sí"])
    )

    data["tipo_caso"] = data["es_recidiva_bool"].map({
        True: t("Recidiva"),
        False: t("Nueva")
    })

    if data.empty:
        return None

    freq, x_title, tickformat = _get_time_bucket_config(rango_rapido, fechas)

    if freq == "SEMANA_MES":
        data["semana_mes"] = ((data["fecha_lesion"].dt.day - 1) // 7) + 1

        grp = (
            data.groupby(["semana_mes", "tipo_caso"])
            .size()
            .reset_index(name="total")
        )

        max_semana = ((data["fecha_lesion"].max().day - 1) // 7) + 1
        full_grid = pd.MultiIndex.from_product(
            [list(range(1, max_semana + 1)), [t("Nueva"), t("Recidiva")]],
            names=["semana_mes", "tipo_caso"]
        ).to_frame(index=False)

        grp = full_grid.merge(grp, on=["semana_mes", "tipo_caso"], how="left").fillna({"total": 0})
        grp["label"] = grp["total"].apply(lambda x: str(int(x)) if x > 0 else "")

        ultimo_dia_mes = pd.to_datetime(data["fecha_lesion"].max()).day
        grp["x_label"] = grp["semana_mes"].apply(lambda x: _label_semana_mes(x, ultimo_dia_mes))

        fig = px.bar(
            grp,
            x="x_label",
            y="total",
            color="tipo_caso",
            barmode="stack",
            text="label",
            title=t("Evolución de nuevas lesiones vs recidivas"),
            color_discrete_map={
                t("Nueva"): "#9ecae1",
                t("Recidiva"): "#d62728",
            }
        )

    else:
        start = data["fecha_lesion"].min()
        end = data["fecha_lesion"].max()

        grp = (
            data.groupby([pd.Grouper(key="fecha_lesion", freq=freq), "tipo_caso"])
            .size()
            .reset_index(name="total")
        )

        full_index = _build_full_period_index(start, end, freq)
        tipos = [t("Nueva"), t("Recidiva")]

        full_grid = pd.MultiIndex.from_product(
            [full_index, tipos],
            names=["fecha_lesion", "tipo_caso"]
        ).to_frame(index=False)

        grp = full_grid.merge(grp, on=["fecha_lesion", "tipo_caso"], how="left").fillna({"total": 0})
        grp["label"] = grp["total"].apply(lambda x: str(int(x)) if x > 0 else "")

        fig = px.bar(
            grp,
            x="fecha_lesion",
            y="total",
            color="tipo_caso",
            barmode="stack",
            text="label",
            title=t("Evolución de nuevas lesiones vs recidivas"),
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
        xaxis_title=x_title,
        yaxis_title=t("Número de lesiones"),
        hovermode="x unified",
        legend_title_text=""
    )

    if freq == "MS":
        fig.update_xaxes(tickformat="%b %Y", dtick="M1")
    elif freq != "SEMANA_MES":
        fig.update_xaxes(tickformat=tickformat)

    return fig


def grafico_evolucion_resumen(
    df: pd.DataFrame,
    rango_rapido: str | None = None,
    fechas: tuple | None = None
):
    if df is None or df.empty or "fecha_lesion" not in df.columns:
        return None

    data = df.copy()
    data["fecha_lesion"] = pd.to_datetime(data["fecha_lesion"], errors="coerce")
    data = data.dropna(subset=["fecha_lesion"]).copy()

    if data.empty:
        return None

    col_player = "id_jugadora" if "id_jugadora" in data.columns else "nombre_jugadora"
    if col_player not in data.columns:
        return None

    impacto_norm = (
        data["impacto_dias_baja_estimado"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        if "impacto_dias_baja_estimado" in data.columns
        else pd.Series("", index=data.index)
    )

    data["grave_flag"] = impacto_norm.eq("GRAVE").astype(int)
    data["muy_grave_flag"] = impacto_norm.eq("MUY GRAVE").astype(int)

    freq, x_title, tickformat = _get_time_bucket_config(rango_rapido, fechas)

    # IMPORTANTE: usar el rango seleccionado, no solo el min/max con datos
    if fechas and fechas[0] and fechas[1]:
        start = pd.to_datetime(fechas[0])
        end = pd.to_datetime(fechas[1])
    else:
        start = data["fecha_lesion"].min()
        end = data["fecha_lesion"].max()

    if freq == "D":
        grp = (
            data.groupby(pd.Grouper(key="fecha_lesion", freq="D"))
            .agg(
                lesiones=("fecha_lesion", "size"),
                jugadoras=(col_player, "nunique"),
                graves=("grave_flag", "sum"),
                muy_graves=("muy_grave_flag", "sum"),
            )
        )

        full_index = pd.date_range(start=start.normalize(), end=end.normalize(), freq="D")
        grp = grp.reindex(full_index, fill_value=0).reset_index()
        grp.columns = ["fecha_lesion", "lesiones", "jugadoras", "graves", "muy_graves"]

        fig = px.bar(
            grp,
            x="fecha_lesion",
            y="lesiones",
            title=t("Evolución de lesiones, jugadoras lesionadas y lesiones graves")
        )

        fig.update_traces(
            name=t("Lesiones registradas"),
            marker_color="#4C78A8"
        )

        fig.add_scatter(
            x=grp["fecha_lesion"],
            y=grp["jugadoras"],
            mode="lines+markers",
            name=t("Jugadoras lesionadas"),
            line=dict(color="#7f8c8d", width=2)
        )

        fig.add_scatter(
            x=grp["fecha_lesion"],
            y=grp["graves"],
            mode="lines+markers",
            name=t("Lesiones graves"),
            line=dict(color="#f39c12", width=2)
        )

        fig.add_scatter(
            x=grp["fecha_lesion"],
            y=grp["muy_graves"],
            mode="lines+markers",
            name=t("Lesiones muy graves"),
            line=dict(color="#e74c3c", width=2)
        )

        fig.update_xaxes(tickformat="%d/%m")

    elif freq == "SEMANA_MES":
        data["semana_mes"] = ((data["fecha_lesion"].dt.day - 1) // 7) + 1

        grp = (
            data.groupby("semana_mes")
            .agg(
                lesiones=("fecha_lesion", "size"),
                jugadoras=(col_player, "nunique"),
                graves=("grave_flag", "sum"),
                muy_graves=("muy_grave_flag", "sum"),
            )
            .reset_index()
        )

        max_semana = ((pd.to_datetime(end).day - 1) // 7) + 1
        full_index = list(range(1, max_semana + 1))

        grp = (
            pd.DataFrame({"semana_mes": full_index})
            .merge(grp, on="semana_mes", how="left")
            .fillna(0)
        )

        ultimo_dia_mes = pd.to_datetime(end).day
        grp["x_label"] = grp["semana_mes"].apply(lambda x: _label_semana_mes(x, ultimo_dia_mes))

        fig = px.bar(
            grp,
            x="x_label",
            y="lesiones",
            title=t("Evolución de lesiones, jugadoras lesionadas y lesiones graves")
        )

        fig.update_traces(
            name=t("Lesiones registradas"),
            marker_color="#4C78A8"
        )

        fig.add_scatter(
            x=grp["x_label"],
            y=grp["jugadoras"],
            mode="lines+markers",
            name=t("Jugadoras lesionadas"),
            line=dict(color="#7f8c8d", width=2)
        )

        fig.add_scatter(
            x=grp["x_label"],
            y=grp["graves"],
            mode="lines+markers",
            name=t("Lesiones graves"),
            line=dict(color="#f39c12", width=2)
        )

        fig.add_scatter(
            x=grp["x_label"],
            y=grp["muy_graves"],
            mode="lines+markers",
            name=t("Lesiones muy graves"),
            line=dict(color="#e74c3c", width=2)
        )

    else:  # MS
        grp = (
            data.groupby(pd.Grouper(key="fecha_lesion", freq="MS"))
            .agg(
                lesiones=("fecha_lesion", "size"),
                jugadoras=(col_player, "nunique"),
                graves=("grave_flag", "sum"),
                muy_graves=("muy_grave_flag", "sum"),
            )
        )

        full_index = pd.date_range(
            start=pd.to_datetime(start).replace(day=1),
            end=pd.to_datetime(end).replace(day=1),
            freq="MS"
        )

        grp = grp.reindex(full_index, fill_value=0).reset_index()
        grp.columns = ["fecha_lesion", "lesiones", "jugadoras", "graves", "muy_graves"]

        fig = px.bar(
            grp,
            x="fecha_lesion",
            y="lesiones",
            title=t("Evolución de lesiones, jugadoras lesionadas y lesiones graves")
        )

        fig.update_traces(
            name=t("Lesiones registradas"),
            marker_color="#4C78A8"
        )

        fig.add_scatter(
            x=grp["fecha_lesion"],
            y=grp["jugadoras"],
            mode="lines+markers",
            name=t("Jugadoras lesionadas"),
            line=dict(color="#7f8c8d", width=2)
        )

        fig.add_scatter(
            x=grp["fecha_lesion"],
            y=grp["graves"],
            mode="lines+markers",
            name=t("Lesiones graves"),
            line=dict(color="#f39c12", width=2)
        )

        fig.add_scatter(
            x=grp["fecha_lesion"],
            y=grp["muy_graves"],
            mode="lines+markers",
            name=t("Lesiones muy graves"),
            line=dict(color="#e74c3c", width=2)
        )

        fig.update_xaxes(tickformat="%b %Y", dtick="M1")

    fig.update_layout(
        template="simple_white",
        height=430,
        xaxis_title=x_title,
        yaxis=dict(
            title=t("Número de casos"),
            rangemode="tozero"
        ),
        hovermode="x unified",
        legend_title_text=""
    )

    return fig

def grafico_evolucion_jugadoras_lesionadas(df: pd.DataFrame, rango_rapido: str | None = None):
    if df is None or df.empty or "fecha_lesion" not in df.columns:
        return None

    data = df.copy()
    data["fecha_lesion"] = pd.to_datetime(data["fecha_lesion"], errors="coerce")
    data = data.dropna(subset=["fecha_lesion"]).copy()

    if data.empty:
        return None

    col_player = "id_jugadora" if "id_jugadora" in data.columns else "nombre_jugadora"
    if col_player not in data.columns:
        return None

    freq, x_title, tickformat = _get_time_bucket_config(rango_rapido)
    start = data["fecha_lesion"].min()
    end = data["fecha_lesion"].max()

    grp = (
        data.groupby(pd.Grouper(key="fecha_lesion", freq=freq))[col_player]
        .nunique()
        .rename("jugadoras_lesionadas")
    )

    full_index = _build_full_period_index(start, end, freq)
    grp = grp.reindex(full_index, fill_value=0).reset_index()
    grp.columns = ["fecha_lesion", "jugadoras_lesionadas"]

    fig = px.line(
        grp,
        x="fecha_lesion",
        y="jugadoras_lesionadas",
        markers=True,
        title=t("Evolución de jugadoras lesionadas")
    )

    fig.update_layout(
        template="simple_white",
        height=420,
        xaxis_title=x_title,
        yaxis_title=t("Número de jugadoras"),
        hovermode="x unified"
    )
    fig.update_xaxes(tickformat=tickformat)

    return fig


def grafico_tipo_por_severidad(df: pd.DataFrame):
    if (
        df is None or df.empty
        or "tipo_lesion" not in df.columns
        or "impacto_dias_baja_estimado" not in df.columns
    ):
        return None

    data = df.copy()
    data["tipo_lesion"] = (
        data["tipo_lesion"]
        .fillna("N/A")
        .astype(str)
        .str.strip()
    )

    # Normalizar días de baja
    if "dias_baja_estimado" in data.columns:
        data["dias_baja_estimado"] = pd.to_numeric(data["dias_baja_estimado"], errors="coerce").fillna(0)
    else:
        data["dias_baja_estimado"] = 0

    # Normalizar severidad
    data["impacto_dias_baja_estimado"] = (
        data["impacto_dias_baja_estimado"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # 0 días -> SIN BAJA
    data.loc[
        (data["impacto_dias_baja_estimado"] == "") & (data["dias_baja_estimado"] == 0),
        "impacto_dias_baja_estimado"
    ] = "SIN BAJA"

    # Si sigue vacío y no es 0 días, dejar como N/A real
    data.loc[
        data["impacto_dias_baja_estimado"] == "",
        "impacto_dias_baja_estimado"
    ] = "N/A"

    # Eliminar categorías que no quieres usar
    data["impacto_dias_baja_estimado"] = data["impacto_dias_baja_estimado"].replace({
        "MENOR": "LEVE",
        "MÍNIMA": "LEVE",
        "MINIMA": "LEVE",
    })

    resumen = (
        data.groupby(["tipo_lesion", "impacto_dias_baja_estimado"])
        .size()
        .reset_index(name="total")
    )

    orden_tipos = (
        resumen.groupby("tipo_lesion")["total"]
        .sum()
        .sort_values(ascending=True)
        .index
        .tolist()
    )

    orden_severidad = [
        "SIN BAJA",
        "LEVE",
        "MODERADA",
        "GRAVE",
        "MUY GRAVE",
        "N/A",
    ]

    resumen["tipo_lesion"] = pd.Categorical(
        resumen["tipo_lesion"],
        categories=orden_tipos,
        ordered=True
    )

    resumen["impacto_dias_baja_estimado"] = pd.Categorical(
        resumen["impacto_dias_baja_estimado"],
        categories=orden_severidad,
        ordered=True
    )

    fig = px.bar(
        resumen.sort_values(["tipo_lesion", "impacto_dias_baja_estimado"]),
        x="total",
        y="tipo_lesion",
        color="impacto_dias_baja_estimado",
        orientation="h",
        barmode="stack",
        text="total",
        title=t("Tipo de lesión por severidad"),
        color_discrete_map={
            "SIN BAJA": "#92b1ce",
            "LEVE": "#2ecc71",
            "MODERADA": "#f1c40f",
            "GRAVE": "#f39c12",
            "MUY GRAVE": "#e74c3c",
            "N/A": "#f1f8f8",
        }
    )

    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle"
    )

    fig.update_layout(
        template="simple_white",
        height=480,
        xaxis_title=t("Número de lesiones"),
        yaxis_title="",
        legend_title_text=t("Severidad"),
    )

    return fig


def grafico_lugar_por_mecanismo(df: pd.DataFrame):
    if (
        df is None or df.empty
        or "lugar" not in df.columns
        or "mecanismo" not in df.columns
    ):
        return None

    data = df.copy()
    data["lugar"] = data["lugar"].fillna("N/A").astype(str).str.strip()
    data["mecanismo"] = data["mecanismo"].fillna("N/A").astype(str).str.strip()

    resumen = (
        data.groupby(["lugar", "mecanismo"])
        .size()
        .reset_index(name="total")
    )

    resumen["label"] = resumen["total"].apply(lambda x: str(int(x)) if x > 0 else "")

    fig = px.bar(
        resumen,
        x="lugar",
        y="total",
        color="mecanismo",
        barmode="stack",
        text="label",
        title=t("Lugar de ocurrencia por mecanismo")
    )

    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle"
    )

    fig.update_layout(
        template="simple_white",
        height=420,
        xaxis_title="",
        yaxis_title=t("Número de lesiones"),
        legend_title_text=t("Mecanismo")
    )

    return fig

def grafico_tipo_por_recidiva(df: pd.DataFrame):
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

    data["es_recidiva_bool"] = (
        data["es_recidiva"]
        .fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "si", "sí"])
    )

    data["tipo_caso"] = data["es_recidiva_bool"].map({
        True: t("Recidiva"),
        False: t("Nueva")
    })

    resumen = (
        data.groupby(["tipo_lesion", "tipo_caso"])
        .size()
        .reset_index(name="total")
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

    resumen["label"] = resumen["total"].apply(lambda x: str(int(x)) if x >= 1 else "")

    fig = px.bar(
        resumen.sort_values(["tipo_lesion", "tipo_caso"]),
        x="total",
        y="tipo_lesion",
        color="tipo_caso",
        orientation="h",
        barmode="stack",
        text="label",
        title=t("Tipo de lesión por recidiva"),
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
        height=460,
        xaxis_title=t("Número de lesiones"),
        yaxis_title="",
        legend_title_text=""
    )

    return fig



COLOR_MAP_ZONAS = {
    "CARA": "#76b7eb",
    "CRÁNEO": "#9ecae1",
    "COLUMNA CERVICAL": "#8c564b",
    "COLUMNA DORSAL": "#2ca89c",
    "TÓRAX": "#f39c12",
    "COLUMNA LUMBAR": "#7f7f7f",
    "PÉLVIS": "#9467bd",
    "CINTURA ESCAPULAR Y HOMBRO": "#ff2b2b",
    "BRAZO": "#1f77b4",
    "CODO": "#f2a7a7",
    "ANTEBRAZO": "#17becf",
    "MUÑECA": "#bcbd22",
    "MANO": "#e377c2",
    "CADERA": "#4e79a7",
    "MUSLO": "#6bdc8b",
    "RODILLA": "#59a14f",
    "PIERNA": "#8cd17d",
    "TOBILLO": "#6f42c1",
    "PIE": "#f4c95d",
    "N/A": "#95a5a6",
}

def completar_color_map_zonas(zonas_presentes: list[str]) -> dict:
    base_map = COLOR_MAP_ZONAS.copy()
    fallback_colors = [
        "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
        "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ab"
    ]

    faltantes = [z for z in zonas_presentes if z not in base_map]
    for i, z in enumerate(faltantes):
        base_map[z] = fallback_colors[i % len(fallback_colors)]

    return base_map

def grafico_impacto_dias_acumulados_por_tipo_y_zona(df: pd.DataFrame):
    if (
        df is None or df.empty
        or "tipo_lesion" not in df.columns
        or "zona_cuerpo" not in df.columns
        or "dias_baja_estimado" not in df.columns
    ):
        return None

    data = df.copy()
    data["dias_baja_estimado"] = pd.to_numeric(data["dias_baja_estimado"], errors="coerce").fillna(0)
    data["tipo_lesion"] = data["tipo_lesion"].fillna("N/A").astype(str).str.strip()
    data["zona_cuerpo"] = data["zona_cuerpo"].fillna("N/A").astype(str).str.strip()

    resumen = (
        data.groupby(["tipo_lesion", "zona_cuerpo"], dropna=False)["dias_baja_estimado"]
        .sum()
        .reset_index()
    )
    resumen.columns = ["tipo_lesion", "zona_cuerpo", "dias_baja"]

    orden_tipos = (
        resumen.groupby("tipo_lesion")["dias_baja"]
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

    resumen["label"] = resumen["dias_baja"].apply(lambda x: f"{x:g}" if x > 0 else "")

    color_map = completar_color_map_zonas(
        sorted(resumen["zona_cuerpo"].dropna().astype(str).unique().tolist())
    )

    fig = px.bar(
        resumen.sort_values(["tipo_lesion", "zona_cuerpo"]),
        x="dias_baja",
        y="tipo_lesion",
        color="zona_cuerpo",
        orientation="h",
        barmode="stack",
        text="label",
        title=t("Días de baja acumulados por tipo de lesión y zona corporal"),
        color_discrete_map=color_map
    )

    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle"
    )

    fig.update_layout(
        template="simple_white",
        height=520,
        xaxis_title=t("Días de baja"),
        yaxis_title="",
        legend_title_text=t("Zona corporal")
    )

    return fig

def grafico_impacto_zona_especifica_detalle(
    df: pd.DataFrame,
    tipo_lesion_sel: str | None = None,
    zona_cuerpo_sel: str | None = None
):
    if (
        df is None or df.empty
        or "dias_baja_estimado" not in df.columns
        or "zona_especifica" not in df.columns
    ):
        return None

    data = df.copy()
    data["dias_baja_estimado"] = pd.to_numeric(
        data["dias_baja_estimado"], errors="coerce"
    ).fillna(0)

    if "tipo_lesion" in data.columns:
        data["tipo_lesion"] = data["tipo_lesion"].fillna("N/A").astype(str).str.strip()
    else:
        data["tipo_lesion"] = "N/A"

    if "zona_cuerpo" in data.columns:
        data["zona_cuerpo"] = data["zona_cuerpo"].fillna("N/A").astype(str).str.strip()
    else:
        data["zona_cuerpo"] = "N/A"

    data["zona_especifica"] = data["zona_especifica"].fillna("N/A").astype(str).str.strip()

    if tipo_lesion_sel and tipo_lesion_sel != t("TODAS"):
        data = data[data["tipo_lesion"] == tipo_lesion_sel]

    if zona_cuerpo_sel and zona_cuerpo_sel != t("TODAS"):
        data = data[data["zona_cuerpo"] == zona_cuerpo_sel]

    if data.empty:
        return None

    resumen = (
        data.groupby(["zona_especifica", "zona_cuerpo"], dropna=False)["dias_baja_estimado"]
        .sum()
        .reset_index()
        .sort_values("dias_baja_estimado", ascending=True)
    )

    resumen["label"] = resumen["dias_baja_estimado"].apply(lambda x: f"{x:g}" if x > 0 else "")

    color_map = completar_color_map_zonas(
        sorted(resumen["zona_cuerpo"].dropna().astype(str).unique().tolist())
    )

    titulo = t("Detalle por zona específica")
    if tipo_lesion_sel and tipo_lesion_sel != t("TODAS"):
        titulo += f" · {tipo_lesion_sel}"
    if zona_cuerpo_sel and zona_cuerpo_sel != t("TODAS"):
        titulo += f" · {zona_cuerpo_sel}"

    fig = px.bar(
        resumen,
        x="dias_baja_estimado",
        y="zona_especifica",
        color="zona_cuerpo",
        orientation="h",
        text="label",
        title=titulo,
        color_discrete_map=color_map
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        template="simple_white",
        height=420,
        xaxis_title=t("Días de baja"),
        yaxis_title="",
        legend_title_text=t("Zona corporal")
    )

    return fig

def grafico_tipo_por_tipo_especifico(df: pd.DataFrame):
    """Heatmap de relación entre tipo de lesión y tipo específico."""
    if (
        df is None or df.empty
        or "tipo_lesion" not in df.columns
        or "tipo_especifico" not in df.columns
    ):
        return None

    data = df.copy()
    data["tipo_lesion"] = (
        data["tipo_lesion"]
        .fillna("N/A")
        .astype(str)
        .str.strip()
    )
    data["tipo_especifico"] = (
        data["tipo_especifico"]
        .fillna("N/A")
        .astype(str)
        .str.strip()
    )

    resumen = (
        data.groupby(["tipo_lesion", "tipo_especifico"])
        .size()
        .reset_index(name="total")
    )

    orden_tipos = (
        resumen.groupby("tipo_lesion")["total"]
        .sum()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    orden_especificos = (
        resumen.groupby("tipo_especifico")["total"]
        .sum()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    fig = px.density_heatmap(
        resumen,
        x="tipo_especifico",
        y="tipo_lesion",
        z="total",
        histfunc="sum",
        text_auto=True,
        title=t("Relación entre tipo de lesión y tipo específico"),
        category_orders={
            "tipo_lesion": orden_tipos,
            "tipo_especifico": orden_especificos,
        }
    )

    fig.update_layout(
        template="simple_white",
        height=520,
        xaxis_title=t("Tipo específico"),
        yaxis_title=t("Tipo de lesión")
    )

    fig.update_xaxes(tickangle=-35)

    return fig

def grafico_impacto_scatter_jugadoras(df: pd.DataFrame):
    if (
        df is None or df.empty
        or "nombre_jugadora" not in df.columns
        or "dias_baja_estimado" not in df.columns
    ):
        return None

    data = df.copy()
    data["dias_baja_estimado"] = pd.to_numeric(data["dias_baja_estimado"], errors="coerce").fillna(0)
    data["nombre_jugadora"] = data["nombre_jugadora"].fillna("N/A").astype(str).str.strip()

    resumen = (
        data.groupby("nombre_jugadora", dropna=False)
        .agg(
            total_lesiones=("nombre_jugadora", "size"),
            dias_baja=("dias_baja_estimado", "sum"),
        )
        .reset_index()
    )
    resumen.columns = ["jugadora", "total_lesiones", "dias_baja"]

    fig = px.scatter(
        resumen,
        x="total_lesiones",
        y="dias_baja",
        text="jugadora",
        title=t("Jugadoras: número de lesiones vs días de baja acumulados")
    )

    fig.update_traces(textposition="top center")

    fig.update_layout(
        template="simple_white",
        height=520,
        xaxis_title=t("Número de lesiones"),
        yaxis_title=t("Días de baja"),
        hovermode="closest"
    )

    return fig


def grafico_tipo_lesion_por_tipo_recidiva(df: pd.DataFrame):
    if (
        df is None or df.empty
        or "tipo_lesion" not in df.columns
        or "es_recidiva" not in df.columns
        or "tipo_recidiva" not in df.columns
    ):
        return None

    data = df.copy()
    data["tipo_lesion"] = (
        data["tipo_lesion"]
        .fillna("N/A")
        .astype(str)
        .str.strip()
    )

    data["tipo_recidiva"] = (
        data["tipo_recidiva"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
    )

    data = data[
        data["es_recidiva"]
        .fillna(False)
        .astype(str)
        .str.strip()
        .str.lower()
        .isin(["true", "1", "si", "sí"])
    ].copy()

    data = data[data["tipo_recidiva"] != ""].copy()

    if data.empty:
        return None

    resumen = (
        data.groupby(["tipo_lesion", "tipo_recidiva"])
        .size()
        .reset_index(name="total")
    )

    orden_tipos = (
        resumen.groupby("tipo_lesion")["total"]
        .sum()
        .sort_values(ascending=False)
        .index
        .tolist()
    )

    orden_recidiva = [
        "TEMPRANA (≤ 2 MESES)",
        "TARDÍA (2-12 MESES)"
    ]

    fig = px.density_heatmap(
        resumen,
        x="tipo_recidiva",
        y="tipo_lesion",
        z="total",
        histfunc="sum",
        text_auto=True,
        title=t("Recidivas tempranas y tardías por tipo de lesión"),
        category_orders={
            "tipo_lesion": orden_tipos,
            "tipo_recidiva": orden_recidiva
        }
    )

    fig.update_layout(
        template="simple_white",
        height=420,
        xaxis_title=t("Tipo de recidiva"),
        yaxis_title=t("Tipo de lesión")
    )

    return fig
    


