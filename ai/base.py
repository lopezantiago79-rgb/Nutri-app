from abc import ABC, abstractmethod

from models.etiqueta import DatosEtiqueta


class ExtractorNutricional(ABC):

    @property
    @abstractmethod
    def proveedor(self) -> str:
        pass

    @property
    @abstractmethod
    def modelo(self) -> str:
        pass

    @abstractmethod
    def extraer(self, ruta_imagen: str) -> DatosEtiqueta:
        pass
