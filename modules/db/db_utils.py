from modules.db.db_connection import get_connection
import streamlit as st

# def fetch_all(query, params=None):
#     """Obtiene múltiples registros."""
#     conn = get_connection()
#     if not conn:
#         return []

#     try:
#         cursor = conn.cursor(dictionary=True)
#         cursor.execute(query, params or ())
#         data = cursor.fetchall()
#         return data
#     except Exception as e:
#         print(f"⚠️ Error en query: {e}")
#         return []
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()

# def execute_query(query, params=None):
#     """Ejecuta INSERT, UPDATE o DELETE."""
#     conn = get_connection()
#     if not conn:
#         return False

#     try:
#         cursor = conn.cursor()
#         cursor.execute(query, params or ())
#         conn.commit()
#         return True
#     except Exception as e:
#         print(f"⚠️ Error en query: {e}")
#         conn.rollback()
#         return False
#     finally:
#         if conn.is_connected():
#             cursor.close()
#             conn.close()


def build_user_access_filter(
    table_alias: str | None = None,
    column: str = "usuario"
):
    """
    Construye el filtro SQL de acceso por usuario según el rol.

    developer → ve todo
    admin → ve todo excepto registros del developer
    otros → solo sus registros

    Retorna:
        sql_filter (str)
        params (tuple)
    """

    rol = st.session_state["auth"]["rol"].lower()
    username = st.session_state["auth"]["username"].lower()

    col = f"{table_alias}.{column}" if table_alias else column

    if rol == "developer":
        return "1=1", ()

    elif rol == "admin":
        return f"{col} != 'developer@developer.com'", ()

    else:
        return f"{col} = %s", (username,)