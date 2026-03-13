import pandas as pd
from modules.db.db_utils import build_user_access_filter
from modules.db.db_connection import get_connection
import streamlit as st
import json
from modules.util.schema import MAP_POSICIONES
from modules.util.util import generar_id_lesion, contar_sesiones

import json
import streamlit as st

def save_lesion(data: dict, modo: str = "nuevo") -> bool:
    """
    Inserta o actualiza una lesión en la base de datos 'lesiones'.

    Parámetros:
        data (dict): Diccionario con todos los campos del registro.
        modo (str): 'nuevo' o 'editar'.

    Retorna:
        bool: True si la operación fue exitosa, False si hubo error.
    """

    conn = get_connection()
    if not conn:
        st.error(":material/warning: No se pudo establecer conexión con la base de datos.")
        return False

    try:
        cursor = conn.cursor(dictionary=True)

        # ============================================================
        # 🔹 Validación de columnas según DDL
        # ============================================================
        columnas_validas = {
            "id_lesion", "id_jugadora", "posicion", "fecha_lesion", "lugar_id",
            "segmento_id", "zona_cuerpo_id", "zona_especifica_id", "lateralidad",
            "tipo_lesion_id", "tipo_especifico_id", "es_recidiva", "tipo_recidiva",
            "dias_baja_estimado", "impacto_dias_baja_estimado", "mecanismo_id",
            "tipo_tratamiento", "personal_reporta", "fecha_alta_diagnostico",
            "fecha_observacion_activa", "fecha_observacion_inactiva", "fecha_alta_medica", 
            "fecha_alta_deportiva", "estado_lesion",
            "diagnostico", "descripcion", "evolucion", "fecha_hora_registro", "usuario"
        }

        # --- Serializar campos JSON ---
        if isinstance(data.get("tipo_tratamiento"), (list, dict)):
            data["tipo_tratamiento"] = json.dumps(data["tipo_tratamiento"], ensure_ascii=False)
        if isinstance(data.get("evolucion"), (list, dict)):
            data["evolucion"] = json.dumps(data["evolucion"], ensure_ascii=False)

        # --- Limpiar campos no válidos ---
        data = {k: v for k, v in data.items() if k in columnas_validas or k == "nombre"}

        # ============================================================
        # 🟢 MODO NUEVO → INSERT
        # ============================================================
        if modo == "nuevo":
            nombre_jugadora = data.get("nombre", "")
            id_last = get_ultima_lesion_id_por_jugadora(data["id_jugadora"])
            id_lesion = generar_id_lesion(nombre_jugadora, data["id_jugadora"], id_last)
            data["id_lesion"] = id_lesion
            data.pop("nombre", None)

            # Validar columnas finales
            data = {k: v for k, v in data.items() if k in columnas_validas}

            query_insert = f"""
            INSERT INTO lesiones ({', '.join(data.keys())})
            VALUES ({', '.join(['%(' + k + ')s' for k in data.keys()])});
            """

            cursor.execute(query_insert, data)
            conn.commit()
            #st.success(f":material/done_all: Lesión **{data['id_lesion']}** insertada correctamente.")
            return True

        # ============================================================
        # 🟡 MODO EDITAR → UPDATE (ya viene con evolución completa)
        # ============================================================
        # elif modo == "editar":
        #     id_lesion = data.get("id_lesion")
        #     if not id_lesion:
        #         st.error(":material/warning: No se proporcionó el ID de la lesión para actualizar.")
        #         return False

        #     params = {
        #         "evolucion": data.get("evolucion"),
        #         "fecha_observacion_activa": data.get("fecha_observacion_activa"),
        #         "fecha_observacion_inactiva": data.get("fecha_observacion_inactiva"),
        #         "fecha_alta_medica": data.get("fecha_alta_medica"),
        #         "fecha_alta_deportiva": data.get("fecha_alta_deportiva"),
        #         "estado_lesion": data.get("estado_lesion"),
        #         "descripcion": data.get("descripcion"),
        #         "id_lesion": id_lesion
        #     }

        #     query_update = """
        #     UPDATE lesiones
        #     SET
        #         evolucion = %(evolucion)s,
        #         fecha_alta_medica = %(fecha_alta_medica)s,
        #         fecha_alta_deportiva = %(fecha_alta_deportiva)s,
        #         fecha_observacion_activa = %(fecha_observacion_activa)s,
        #         fecha_observacion_inactiva = %(fecha_observacion_inactiva)s,
        #         estado_lesion = %(estado_lesion)s,
        #         descripcion = %(descripcion)s,
        #         updated_at = CURRENT_TIMESTAMP
        #     WHERE id_lesion = %(id_lesion)s;
        #     """

        #     # --- Modo developer: mostrar query y params ---
        #     #if st.session_state.get("auth", {}).get("rol").lower() == "developer":
        #     if st.session_state["auth"]["rol"].lower() == "developer":    
        #         st.write("🟡 Query UPDATE ejecutada:")
        #         st.code(query_update, language="sql")
        #         st.json(params)

        #     cursor.execute(query_update, params)
        #     conn.commit()
        #     #st.success(f":material/done_all: Lesión **{id_lesion}** actualizada correctamente.")
        #     return True

        elif modo == "editar":

            id_lesion = data.get("id_lesion")

            if not id_lesion:
                st.error(":material/warning: No se proporcionó el ID de la lesión para actualizar.")
                return False

            # eliminar campos que no deben actualizarse
            data.pop("nombre", None)
            data.pop("id", None)

            # construir query dinámica
            columnas_update = [k for k in data.keys() if k != "id_lesion"]

            set_clause = ", ".join([f"{col} = %({col})s" for col in columnas_update])

            query_update = f"""
                UPDATE lesiones
                SET
                    {set_clause},
                    updated_at = CURRENT_TIMESTAMP
                WHERE id_lesion = %(id_lesion)s;
            """

            # --- debug developer ---
            if st.session_state["auth"]["rol"].lower() == "developer":
                st.write("🟡 Query UPDATE ejecutada:")
                st.code(query_update, language="sql")
                st.json(data)

            cursor.execute(query_update, data)
            conn.commit()

            return True
        else:
            st.warning(":material/warning: Modo no reconocido. Use 'nuevo' o 'editar'.")
            return False

    except Exception as e:
        conn.rollback()
        st.error(f":material/warning: Error al guardar la lesión: {e}")

        if st.session_state.get("auth", {}).get("rol") == "developer":
            st.json(data)

        return False

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def load_lesiones_db(as_df=True):
    """
    Carga registros de lesiones con joins incluidos y control de acceso por usuario.
    """

    conn = get_connection()
    if not conn:
        st.error(":material/warning: No se pudo conectar a la base de datos.")
        return pd.DataFrame() if as_df else []

    try:

        # ----------------------------
        # Control de acceso reutilizable
        # ----------------------------
        user_filter, user_params = build_user_access_filter("l")

        sql = f"""
        SELECT 
            l.id,
            l.id_lesion,
            l.id_jugadora AS id_jugadora,
            f.nombre,
            f.apellido,
            l.posicion,
            l.fecha_lesion,
            lu.nombre AS lugar,
            s.nombre AS segmento,
            z.nombre AS zona_cuerpo,
            za.nombre AS zona_especifica,
            l.lateralidad,
            t.nombre AS tipo_lesion,
            te.nombre AS tipo_especifico,
            l.es_recidiva,
            l.tipo_recidiva,
            l.dias_baja_estimado,
            l.impacto_dias_baja_estimado,
            m.nombre AS mecanismo,
            l.tipo_tratamiento,
            l.personal_reporta,
            l.fecha_alta_diagnostico,
            l.fecha_alta_deportiva,
            l.fecha_alta_medica,
            l.fecha_observacion_activa,
            l.fecha_observacion_inactiva,
            l.estado_lesion,
            l.diagnostico,
            l.descripcion,
            l.evolucion,
            l.fecha_hora_registro,
            l.usuario

        FROM lesiones l
        LEFT JOIN futbolistas f ON l.id_jugadora = f.identificacion
        LEFT JOIN lugares lu ON l.lugar_id = lu.id
        LEFT JOIN segmentos_corporales s ON l.segmento_id = s.id
        LEFT JOIN zonas_segmento z ON l.zona_cuerpo_id = z.id
        LEFT JOIN zonas_anatomicas za ON l.zona_especifica_id = za.id
        LEFT JOIN tipo_lesion t ON l.tipo_lesion_id = t.id
        LEFT JOIN tipo_especifico_lesion te ON l.tipo_especifico_id = te.id
        LEFT JOIN mecanismos m ON l.mecanismo_id = m.id

        WHERE f.id_estado = 1
          AND {user_filter}

        ORDER BY l.fecha_hora_registro DESC
        """

        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, user_params)

        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            st.info(":material/info: No existen registros de lesiones en la base de datos.")
            return pd.DataFrame() if as_df else []

        df = pd.DataFrame(rows)

        # ----------------------------
        # Procesamiento adicional
        # ----------------------------
        # Normalización
        df["nombre"] = df["nombre"].astype(str).str.strip().str.title()
        df["apellido"] = df["apellido"].astype(str).str.strip().str.title()

        df["nombre_jugadora"] = (df["nombre"] + " " + df["apellido"]).str.strip().str.upper()

        df["sesiones"] = df["evolucion"].apply(contar_sesiones)
        df["posicion"] = df["posicion"].map(MAP_POSICIONES).fillna(df["posicion"])

        return df if as_df else df.to_dict(orient="records")

    except Exception as e:
        st.error(f":material/warning: Error al cargar lesiones: {e}")
        return pd.DataFrame() if as_df else []

    finally:
        conn.close()


def get_ultima_lesion_id_por_jugadora(id_jugadora: str) -> str | None:
    """
    Devuelve el ID de la última lesión registrada de una jugadora
    respetando el control de acceso del sistema.
    """

    conn = get_connection()
    if not conn:
        st.error(":material/warning: No se pudo conectar a la base de datos.")
        return None

    try:

        # control de acceso
        user_filter, user_params = build_user_access_filter("l")

        query = f"""
        SELECT l.id_lesion
        FROM lesiones l
        LEFT JOIN futbolistas f ON l.id_jugadora = f.identificacion
        WHERE l.id_jugadora = %s
          AND f.id_estado = 1
          AND {user_filter}
        ORDER BY COALESCE(l.fecha_hora_registro, l.fecha_lesion) DESC
        LIMIT 1;
        """

        cursor = conn.cursor()
        cursor.execute(query, (id_jugadora, *user_params))
        result = cursor.fetchone()

        return result[0] if result else None

    except Exception as e:
        st.error(f":material/warning: Error al obtener el ID de la última lesión: {e}")
        return None

    finally:
        if conn:
            conn.close()


def get_records_plus_players_db(plantel: str = None) -> pd.DataFrame:
    """
    Devuelve todas las lesiones junto con los datos de las jugadoras.
    Aplica control de acceso por usuario.
    """

    conn = get_connection()
    if not conn:
        st.error(":material/warning: No se pudo conectar a la base de datos.")
        return pd.DataFrame()

    try:

        # control de acceso
        user_filter, user_params = build_user_access_filter("l")

        query = f"""
        SELECT 
            l.id AS id_registro,
            l.id_lesion,
            l.id_jugadora,
            f.nombre,
            f.apellido,
            f.competicion AS plantel,
            i.posicion,
            l.fecha_lesion,
            l.estado_lesion,
            l.diagnostico,
            l.dias_baja_estimado,
            l.impacto_dias_baja_estimado,
            l.mecanismo_id,
            m.nombre AS mecanismo,
            t.nombre AS tipo_lesion,
            te.nombre AS tipo_especifico,
            l.lugar_id,
            lu.nombre AS lugar,
            l.segmento_id,
            s.nombre AS segmento,
            l.zona_cuerpo_id,
            z.nombre AS zona_cuerpo,
            l.zona_especifica_id,
            za.nombre AS zona_especifica,
            l.lateralidad,
            l.es_recidiva,
            l.tipo_recidiva,
            l.tipo_tratamiento,
            l.personal_reporta,
            l.fecha_alta_diagnostico,
            l.fecha_alta_medica,
            l.fecha_alta_deportiva,
            l.descripcion,
            l.evolucion,
            l.fecha_hora_registro,
            l.usuario

        FROM lesiones l
        LEFT JOIN futbolistas f ON l.id_jugadora = f.identificacion
        LEFT JOIN informacion_futbolistas i ON l.id_jugadora = i.identificacion
        LEFT JOIN lugares lu ON l.lugar_id = lu.id
        LEFT JOIN mecanismos m ON l.mecanismo_id = m.id
        LEFT JOIN tipo_lesion t ON l.tipo_lesion_id = t.id
        LEFT JOIN tipo_especifico_lesion te ON l.tipo_especifico_id = te.id
        LEFT JOIN segmentos_corporales s ON l.segmento_id = s.id
        LEFT JOIN zonas_segmento z ON l.zona_cuerpo_id = z.id
        LEFT JOIN zonas_anatomicas za ON l.zona_especifica_id = za.id

        WHERE f.id_estado = 1
          AND {user_filter}

        ORDER BY l.fecha_hora_registro DESC
        """

        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, user_params)

        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            st.info(":material/info: No existen registros de lesiones en la base de datos.")
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # -------------------------
        # Campos calculados
        # -------------------------

        df["nombre_jugadora"] = (
            df["nombre"].fillna("") + " " + df["apellido"].fillna("")
        ).str.strip().str.upper()

        columnas = df.columns.tolist()

        if "id_jugadora" in columnas and "nombre_jugadora" in columnas:
            idx = columnas.index("id_jugadora") + 1
            columnas.insert(idx, columnas.pop(columnas.index("nombre_jugadora")))

        if "posicion" in columnas and "plantel" in columnas:
            idx = columnas.index("posicion") + 1
            columnas.insert(idx, columnas.pop(columnas.index("plantel")))

        df = df[columnas]

        df["posicion"] = df["posicion"].map(MAP_POSICIONES).fillna(df["posicion"])
        df["sesiones"] = df["evolucion"].apply(contar_sesiones)

        if plantel:
            df = df[df["plantel"] == plantel]

        return df

    except Exception as e:
        st.error(f":material/warning: Error al cargar registros y jugadoras: {e}")
        return pd.DataFrame()

    finally:
        conn.close()


def delete_lesiones(ids: list[int]) -> tuple[bool, str]:
    """
    Elimina múltiples lesiones desde la base de datos.

    Parámetros:
        ids (list[int]): lista de IDs de lesiones a eliminar.

    Retorna:
        (bool, str): (éxito, mensaje)
    """
    if not ids:
        return False, "No se proporcionaron IDs de lesiones."
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Construir la query dinámica con placeholders
        query = f"DELETE FROM lesiones WHERE id_lesion IN ({','.join(['%s'] * len(ids))})"
        cursor.execute(query, tuple(ids))
        conn.commit()

        cursor.close()
        conn.close()

        return True, f"Se eliminaron {cursor.rowcount} registro(s) correctamente."

    except Exception as e:
        print(f"Error al eliminar lesiones: {e}")
        st.error(f":material/warning: Error al eliminar lesiones: {e}")
        return False, f":material/warning: Error al eliminar lesiones: {e}"
