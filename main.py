import json
from pathlib import Path

from models.etiqueta import DatosEtiqueta
from models.perfil import PerfilNutricional
from nutrition.evaluator import evaluar_producto
from ai.mock import MockExtractor


BASE_DIR = Path(__file__).resolve().parent


def cargar_perfil(ruta: Path) -> PerfilNutricional:
    with open(ruta, "r", encoding="utf-8") as archivo:
        datos = json.load(archivo)

    if not datos.get("perfiles"):
        raise ValueError("No se encontraron perfiles nutricionales.")

    return PerfilNutricional.model_validate(datos["perfiles"][0])


def crear_etiqueta_de_prueba() -> DatosEtiqueta:
    return DatosEtiqueta(
        producto_detectado="Galletitas de prueba",
        tamano_porcion_g=30,
        sodio_mg_por_porcion=95,
        azucares_g_por_porcion=4,
        grasas_g_por_porcion=6,
        grasas_saturadas_g_por_porcion=2,
        fibra_g_por_porcion=2,
        carbohidratos_g_por_porcion=20,
        proteinas_g_por_porcion=3,
        ingredientes_detectados=[
            "harina de trigo",
            "agua",
            "aceite vegetal",
            "sal",
        ],
        contiene_azucares_anadidos=False,
        contiene_maltodextrina=False,
        contiene_jarabe_maiz_alta_fructosa=False,
        contiene_gluten=True,
        contiene_leche=False,
        contiene_huevo=False,
        texto_no_legible=False,
        advertencias_lectura=[],
    )


def main() -> None:

    ruta_perfil = BASE_DIR / "profiles" / "perfiles_demo.json"

    perfil = cargar_perfil(ruta_perfil)

    datos_prueba = crear_etiqueta_de_prueba()

    extractor = MockExtractor(datos_prueba)

    datos_extraidos = extractor.extraer("imagen_de_prueba.jpg")

    resultado = evaluar_producto(
        datos=datos_extraidos,
        perfil=perfil,
        proveedor_ia=extractor.proveedor,
        modelo_ia=extractor.modelo,
    )

    print("\n========================================")
    print("        NUTRI APP — PRUEBA V0.1")
    print("========================================")

    print(f"\nProducto: {resultado.producto_detectado}")
    print(f"Estado:   {resultado.estado.value}")
    print(f"Motivo:   {resultado.motivo}")

    print("\nReglas evaluadas:")

    for regla in resultado.reglas_evaluadas:
        print(
            f"  - {regla.regla}: "
            f"{regla.cumplida} — {regla.detalle}"
        )

    if resultado.advertencias:
        print("\nAdvertencias:")

        for advertencia in resultado.advertencias:
            print(f"  - {advertencia}")

    print("\n========================================\n")


if __name__ == "__main__":
    main()
