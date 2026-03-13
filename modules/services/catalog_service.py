from modules.db.db_catalogs import load_catalog_list_db
from modules.util.io_files import load_catalog_list


def load_lesion_catalogs():
    """
    Carga todos los catálogos necesarios para el formulario de lesiones.
    Centraliza la lógica de acceso a catálogos.
    """

    # -------------------------
    # Segmentos corporales
    # -------------------------
    segmentos_df = load_catalog_list_db("segmentos_corporales", as_df=True)
    segmentos_list = segmentos_df["nombre"].tolist()
    map_segmentos = dict(zip(segmentos_df["nombre"], segmentos_df["id"]))

    # -------------------------
    # Zonas
    # -------------------------
    zonas_segmento_df = load_catalog_list_db("zonas_segmento", as_df=True)
    map_zonas_segmento = dict(zip(zonas_segmento_df["nombre"], zonas_segmento_df["id"]))

    zonas_anatomicas_df = load_catalog_list_db("zonas_anatomicas", as_df=True)
    map_zonas_anatomicas = dict(zip(zonas_anatomicas_df["nombre"], zonas_anatomicas_df["id"]))

    # -------------------------
    # Mecanismos
    # -------------------------
    mecanismos_df = load_catalog_list_db("mecanismos", as_df=True)
    mecanismos_list = mecanismos_df["nombre"].tolist()
    map_mecanismos = dict(zip(mecanismos_df["nombre"], mecanismos_df["id"]))

    # -------------------------
    # Tipos de lesión
    # -------------------------
    tipos_df = load_catalog_list_db("tipo_lesion", as_df=True)
    map_tipos = dict(zip(tipos_df["nombre"], tipos_df["id"]))

    subtipos_df = load_catalog_list_db("tipo_especifico_lesion", as_df=True)
    map_subtipos = dict(zip(subtipos_df["nombre"], subtipos_df["id"]))

    relacion_df = load_catalog_list_db("mecanismo_tipo_lesion", as_df=True)

    # -------------------------
    # Tratamientos
    # -------------------------
    tratamientos_df = load_catalog_list_db("tratamientos", as_df=True)
    tratamientos_list = tratamientos_df["nombre"].tolist()

    # -------------------------
    # Lugares
    # -------------------------
    lugares_df = load_catalog_list_db("lugares", as_df=True)
    lugares_list = lugares_df["nombre"].tolist()
    map_lugares = dict(zip(lugares_df["nombre"], lugares_df["id"]))

    # -------------------------
    # Otros catálogos
    # -------------------------
    lateralidades = load_catalog_list("lateralidades")
    tipos_recidiva = load_catalog_list("tipos_recidiva")

    gravedad_df = load_catalog_list("gravedad", as_df=True)
    gravedad_dias = (
        gravedad_df.set_index("nombre")[["dias_min", "dias_max"]]
        .apply(tuple, axis=1)
        .to_dict()
    )

    return {
        "segmentos_df": segmentos_df,
        "segmentos_list": segmentos_list,
        "map_segmentos": map_segmentos,

        "zonas_segmento_df": zonas_segmento_df,
        "map_zonas_segmento": map_zonas_segmento,

        "zonas_anatomicas_df": zonas_anatomicas_df,
        "map_zonas_anatomicas": map_zonas_anatomicas,

        "mecanismos_df": mecanismos_df,
        "mecanismos_list": mecanismos_list,
        "map_mecanismos": map_mecanismos,

        "tipos_df": tipos_df,
        "map_tipos": map_tipos,

        "subtipos_df": subtipos_df,
        "map_subtipos": map_subtipos,

        "relacion_df": relacion_df,

        "tratamientos_list": tratamientos_list,

        "lugares_list": lugares_list,
        "map_lugares": map_lugares,

        "lateralidades": lateralidades,
        "tipos_recidiva": tipos_recidiva,

        "gravedad_dias": gravedad_dias,
    }