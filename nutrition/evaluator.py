from models.etiqueta import DatosEtiqueta
from models.perfil import PerfilNutricional
from models.resultado import (
    EstadoEvaluacion,
    ResultadoEvaluacion,
    ResultadoRegla,
)

from .normalizer import contiene_ingrediente


MAPA_NUTRIENTES = {
    "sodio": "sodio_mg_por_porcion",
    "azucares": "azucares_g_por_porcion",
    "grasas": "grasas_g_por_porcion",
    "grasas_saturadas": "grasas_saturadas_g_por_porcion",
    "fibra": "fibra_g_por_porcion",
    "carbohidratos": "carbohidratos_g_por_porcion",
    "proteinas": "proteinas_g_por_porcion",
}


def evaluar_regla_numerica(
    datos: DatosEtiqueta,
    nutriente: str,
    maximo: float | None,
    minimo: float | None,
    unidad: str,
    descripcion: str,
) -> ResultadoRegla:

    campo = MAPA_NUTRIENTES.get(nutriente)

    if campo is None:
        return ResultadoRegla(
            regla=descripcion or nutriente,
            cumplida=None,
            valor_detectado=None,
            limite=None,
            unidad=unidad,
            detalle=f"Nutriente no reconocido: {nutriente}",
        )

    valor = getattr(datos, campo, None)

    if valor is None:
        return ResultadoRegla(
            regla=descripcion or nutriente,
            cumplida=None,
            valor_detectado=None,
            limite=maximo if maximo is not None else minimo,
            unidad=unidad,
            detalle=f"No se pudo determinar el valor de {nutriente}.",
        )

    if maximo is not None and valor > maximo:
        return ResultadoRegla(
            regla=descripcion or nutriente,
            cumplida=False,
            valor_detectado=valor,
            limite=maximo,
            unidad=unidad,
            detalle=(
                f"{nutriente}: {valor} {unidad}, "
                f"supera el máximo permitido de {maximo} {unidad}."
            ),
        )

    if minimo is not None and valor < minimo:
        return ResultadoRegla(
            regla=descripcion or nutriente,
            cumplida=False,
            valor_detectado=valor,
            limite=minimo,
            unidad=unidad,
            detalle=(
                f"{nutriente}: {valor} {unidad}, "
                f"está por debajo del mínimo requerido de {minimo} {unidad}."
            ),
        )

    return ResultadoRegla(
        regla=descripcion or nutriente,
        cumplida=True,
        valor_detectado=valor,
        limite=maximo if maximo is not None else minimo,
        unidad=unidad,
        detalle=f"{nutriente}: {valor} {unidad}. Regla cumplida.",
    )


def evaluar_producto(
    datos: DatosEtiqueta,
    perfil: PerfilNutricional,
    proveedor_ia: str = "desconocido",
    modelo_ia: str = "desconocido",
) -> ResultadoEvaluacion:

    reglas_evaluadas: list[ResultadoRegla] = []
    reglas_incumplidas: list[str] = []
    advertencias: list[str] = []

    # ---------------------------------------------------------
    # 1. Reglas numéricas
    # ---------------------------------------------------------

    for regla in perfil.reglas_numericas:

        resultado = evaluar_regla_numerica(
            datos=datos,
            nutriente=regla.nutriente,
            maximo=regla.maximo,
            minimo=regla.minimo,
            unidad=regla.unidad,
            descripcion=regla.descripcion,
        )

        reglas_evaluadas.append(resultado)

        if resultado.cumplida is False:
            reglas_incumplidas.append(resultado.regla)

        if resultado.cumplida is None:
            advertencias.append(resultado.detalle)

    # ---------------------------------------------------------
    # 2. Ingredientes prohibidos
    # ---------------------------------------------------------

    for ingrediente in perfil.ingredientes_prohibidos:

        if contiene_ingrediente(
            datos.ingredientes_detectados,
            ingrediente,
        ):
            regla = f"Ingrediente prohibido: {ingrediente}"

            reglas_incumplidas.append(regla)

            reglas_evaluadas.append(
                ResultadoRegla(
                    regla=regla,
                    cumplida=False,
                    detalle=(
                        f"Se detectó el ingrediente prohibido "
                        f"'{ingrediente}'."
                    ),
                )
            )

    # ---------------------------------------------------------
    # 3. Restricciones específicas
    # ---------------------------------------------------------

    restricciones = [
        (
            perfil.prohibir_azucares_anadidos,
            datos.contiene_azucares_anadidos,
            "Azúcares añadidos",
        ),
        (
            perfil.prohibir_maltodextrina,
            datos.contiene_maltodextrina,
            "Maltodextrina",
        ),
        (
            perfil.prohibir_jarabe_maiz_alta_fructosa,
            datos.contiene_jarabe_maiz_alta_fructosa,
            "Jarabe de maíz de alta fructosa",
        ),
        (
            perfil.prohibir_gluten,
            datos.contiene_gluten,
            "Gluten",
        ),
        (
            perfil.prohibir_leche,
            datos.contiene_leche,
            "Leche",
        ),
        (
            perfil.prohibir_huevo,
            datos.contiene_huevo,
            "Huevo",
        ),
    ]

    for prohibida, detectada, nombre in restricciones:

        if not prohibida:
            continue

        regla = f"Prohibición: {nombre}"

        if detectada is True:

            reglas_incumplidas.append(regla)

            reglas_evaluadas.append(
                ResultadoRegla(
                    regla=regla,
                    cumplida=False,
                    detalle=f"Se detectó {nombre}.",
                )
            )

        elif detectada is False:

            reglas_evaluadas.append(
                ResultadoRegla(
                    regla=regla,
                    cumplida=True,
                    detalle=f"No se detectó {nombre}.",
                )
            )

        else:

            reglas_evaluadas.append(
                ResultadoRegla(
                    regla=regla,
                    cumplida=None,
                    detalle=(
                        f"No se pudo determinar con seguridad "
                        f"si contiene {nombre}."
                    ),
                )
            )

            advertencias.append(
                f"No se pudo verificar {nombre}."
            )

    # ---------------------------------------------------------
    # 4. Legibilidad
    # ---------------------------------------------------------

    if datos.texto_no_legible:
        advertencias.append(
            "Una parte importante de la etiqueta no es legible."
        )

    advertencias.extend(datos.advertencias_lectura)

    # ---------------------------------------------------------
    # 5. Decisión final
    # ---------------------------------------------------------

    if reglas_incumplidas:

        estado = EstadoEvaluacion.NO_APTO

        motivo = (
            "El producto incumple una o más reglas del "
            "perfil nutricional."
        )

    elif advertencias:

        estado = EstadoEvaluacion.REVISION_MANUAL

        motivo = (
            "No se puede determinar la aptitud con suficiente "
            "certeza debido a información incompleta o ilegible."
        )

    else:

        estado = EstadoEvaluacion.APTO

        motivo = (
            "El producto cumple todas las reglas evaluadas "
            "del perfil nutricional."
        )

    return ResultadoEvaluacion(
        producto_detectado=datos.producto_detectado,
        estado=estado,
        motivo=motivo,
        reglas_evaluadas=reglas_evaluadas,
        reglas_incumplidas=reglas_incumplidas,
        advertencias=advertencias,
        datos_extraidos=datos,
        proveedor_ia=proveedor_ia,
        modelo_ia=modelo_ia,
    )
