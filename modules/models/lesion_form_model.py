from dataclasses import dataclass
from typing import Optional, List


@dataclass
class LesionFormModel:

    # identificación
    fecha_lesion: str
    lugar_id: Optional[int]
    segmento_id: Optional[int]
    zona_cuerpo_id: Optional[int]
    zona_especifica_id: Optional[int]

    # clasificación
    lateralidad: Optional[str]
    tipo_lesion_id: Optional[int]
    tipo_especifico_id: Optional[int]
    mecanismo_id: Optional[int]

    # clínica
    es_recidiva: bool
    tipo_recidiva: Optional[str]

    # impacto
    dias_baja_estimado: int
    gravedad: Optional[str]

    # tratamiento
    tratamientos: List[str]

    # diagnóstico
    diagnostico: Optional[str]
    descripcion: Optional[str]

    # personal
    personal_reporta: str

    # fechas
    fecha_alta_diagnostico: Optional[str]

    # estado
    estado_lesion: str