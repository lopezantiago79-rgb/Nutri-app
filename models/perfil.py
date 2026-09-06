from typing import Optional

from pydantic import BaseModel, Field


class ReglaNumerica(BaseModel):
    nutriente: str
    maximo: Optional[float] = None
    minimo: Optional[float] = None
    unidad: str
    por: str = "porcion"
    descripcion: str = ""


class PerfilNutricional(BaseModel):
    id_perfil: str
    nombre: str
    descripcion: str = ""

    reglas_numericas: list[ReglaNumerica] = Field(
        default_factory=list
    )

    ingredientes_prohibidos: list[str] = Field(
        default_factory=list
    )

    ingredientes_permitidos: list[str] = Field(
        default_factory=list
    )

    prohibir_azucares_anadidos: bool = False
    prohibir_maltodextrina: bool = False
    prohibir_jarabe_maiz_alta_fructosa: bool = False
    prohibir_gluten: bool = False
    prohibir_leche: bool = False
    prohibir_huevo: bool = False
