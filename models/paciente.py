from datetime import datetime

from pydantic import BaseModel, Field

from .perfil import PerfilNutricional


class Paciente(BaseModel):
    """
    Modelo de dominio de un paciente.

    Este archivo contiene únicamente la estructura de datos.
    No debe ejecutar lógica de Streamlit ni acceder a archivos.
    """

    id_paciente: str = Field(
        description="Identificador único del paciente."
    )

    nombre: str = Field(
        min_length=1,
        description="Nombre del paciente."
    )

    descripcion: str = Field(
        default="",
        description="Descripción o indicaciones generales del paciente."
    )

    perfil: PerfilNutricional | None = Field(
        default=None,
        description="Perfil nutricional actualmente configurado."
    )

    fecha_creacion: datetime = Field(
        default_factory=datetime.now,
        description="Fecha y hora de creación del paciente."
    )

    activo: bool = Field(
        default=True,
        description="Indica si el paciente está activo."
    )
