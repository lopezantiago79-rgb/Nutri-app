from typing import Optional

from pydantic import BaseModel, Field


class DatosEtiqueta(BaseModel):
    producto_detectado: str = Field(
        description="Nombre o tipo de producto identificado."
    )

    tamano_porcion_g: Optional[float] = Field(
        default=None,
        description="Tamaño de la porción en gramos."
    )

    sodio_mg_por_porcion: Optional[float] = Field(
        default=None,
        description="Sodio en miligramos por porción."
    )

    azucares_g_por_porcion: Optional[float] = Field(
        default=None,
        description="Azúcares totales en gramos por porción."
    )

    grasas_g_por_porcion: Optional[float] = Field(
        default=None,
        description="Grasas totales en gramos por porción."
    )

    grasas_saturadas_g_por_porcion: Optional[float] = Field(
        default=None,
        description="Grasas saturadas en gramos por porción."
    )

    fibra_g_por_porcion: Optional[float] = Field(
        default=None,
        description="Fibra en gramos por porción."
    )

    carbohidratos_g_por_porcion: Optional[float] = Field(
        default=None,
        description="Carbohidratos en gramos por porción."
    )

    proteinas_g_por_porcion: Optional[float] = Field(
        default=None,
        description="Proteínas en gramos por porción."
    )

    ingredientes_detectados: list[str] = Field(
        default_factory=list,
        description="Ingredientes visibles en la etiqueta."
    )

    contiene_azucares_anadidos: Optional[bool] = Field(default=None)

    contiene_maltodextrina: Optional[bool] = Field(default=None)

    contiene_jarabe_maiz_alta_fructosa: Optional[bool] = Field(default=None)

    contiene_gluten: Optional[bool] = Field(default=None)

    contiene_leche: Optional[bool] = Field(default=None)

    contiene_huevo: Optional[bool] = Field(default=None)

    texto_no_legible: bool = Field(
        default=False,
        description=(
            "True si una parte importante de la etiqueta "
            "no puede leerse con seguridad."
        )
    )

    advertencias_lectura: list[str] = Field(
        default_factory=list
    )
