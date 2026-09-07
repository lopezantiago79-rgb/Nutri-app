import unicodedata


def normalizar_texto(texto: str) -> str:
    texto = texto.lower().strip()

    texto = unicodedata.normalize("NFD", texto)

    texto = "".join(
        caracter
        for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )

    return texto


def contiene_ingrediente(
    ingredientes: list[str],
    buscado: str
) -> bool:
    buscado = normalizar_texto(buscado)

    return any(
        buscado in normalizar_texto(ingrediente)
        for ingrediente in ingredientes
    )
