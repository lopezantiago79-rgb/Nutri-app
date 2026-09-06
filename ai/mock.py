from models.etiqueta import DatosEtiqueta

from .base import ExtractorNutricional


class MockExtractor(ExtractorNutricional):

    def __init__(self, datos: DatosEtiqueta):
        self.datos = datos

    @property
    def proveedor(self) -> str:
        return "Mock"

    @property
    def modelo(self) -> str:
        return "mock-v1"

    def extraer(self, ruta_imagen: str) -> DatosEtiqueta:
        return self.datos
