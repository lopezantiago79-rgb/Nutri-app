from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .etiqueta import DatosEtiqueta


class EstadoEvaluacion(str, Enum):
    APTO = "APTO"
    NO_APTO = "NO_APTO"
    REVISION_MANUAL = "REVISION_MANUAL"


class ResultadoRegla(BaseModel):
    regla: str
    cumplida: Optional[bool]
    valor_detectado: Optional[float] = None
    limite: Optional[float] = None
    unidad: Optional[str] = None
    detalle: str


class ResultadoEvaluacion(BaseModel):
    producto_detectado: str
    estado: EstadoEvaluacion
    motivo: str

    reglas_evaluadas: list[ResultadoRegla] = Field(
        default_factory=list
    )

    reglas_incumplidas: list[str] = Field(
        default_factory=list
    )

    advertencias: list[str] = Field(
        default_factory=list
    )

    datos_extraidos: DatosEtiqueta

    proveedor_ia: str
    modelo_ia: str
