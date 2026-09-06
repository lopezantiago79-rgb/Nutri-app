import mimetypes
import os 

from google import genai
from google.genai import types

from models.etiqueta import DatosEtiqueta

from .base import ExtractorNutricional


PROMPT_EXTRACCION = """
Analiza cuidadosamente esta etiqueta nutricional.

Tu única tarea es EXTRAER información.

NO determines si el producto es apto.
NO evalúes ninguna dieta.
NO hagas recomendaciones médicas.

Extrae exclusivamente información visible en la imagen.

REGLAS:

1. No inventes valores.
2. Si un valor numérico no puede leerse con seguridad, devuelve null.
3. Si una parte importante de la etiqueta no puede leerse correctamente,
   marca texto_no_legible=true.
4. Extrae la tabla nutricional.
5. Extrae la lista de ingredientes.
6. Identifica, cuando exista evidencia suficiente:
   - azúcar añadido
   - maltodextrina
   - jarabe de maíz de alta fructosa
   - gluten
   - leche
   - huevo
7. Si existe una duda importante, descríbela en advertencias_lectura.
8. No realices ninguna evaluación clínica.
"""


class GeminiExtractor(ExtractorNutricional):

    def __init__(self, model: str = "gemini-2.5-flash"):
        self._model = model

        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "No se encontró GEMINI_API_KEY en las variables de entorno."
            )

        self.client = genai.Client(api_key=api_key)

    @property
    def proveedor(self) -> str:
        return "Google Gemini"

    @property
    def modelo(self) -> str:
        return self._model

    def extraer(self, ruta_imagen: str) -> DatosEtiqueta:

        with open(ruta_imagen, "rb") as f:
            imagen = f.read()

        mime_type, _ = mimetypes.guess_type(ruta_imagen)

        if mime_type is None:
            mime_type = "image/jpeg"

        response = self.client.models.generate_content(
            model=self._model,
            contents=[
                PROMPT_EXTRACCION,
                types.Part.from_bytes(
                    data=imagen,
                    mime_type=mime_type
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DatosEtiqueta,
                temperature=0.0
            )
        )

        if not response.text:
            raise RuntimeError(
                "Gemini no devolvió una respuesta de texto válida."
            )

        return DatosEtiqueta.model_validate_json(response.text)
