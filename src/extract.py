"""Paso 1 - PDF a texto, PAGINA POR PAGINA.

Diferencia clave con el notebook original: aqui NO concatenamos todo en un
solo string con marcadores [PAGE N] dentro del texto. Devolvemos una lista
de paginas. El numero de pagina viajara como METADATO, no como texto.

Motivo medido: con el enfoque anterior, solo el 9.3% de los fragmentos
conservaba el marcador. El 90.7% restante no podia citar su pagina, y el
modelo terminaba atribuyendo la respuesta a una pagina equivocada.
"""

from __future__ import annotations
import re
import pypdf


def limpiar(texto: str) -> str:
    """Normaliza el texto crudo que devuelve pypdf."""
    texto = re.sub(r" {2,}", " ", texto)          # espacios multiples
    texto = re.sub(r"(?<!\n)\n(?!\n)", " ", texto)  # saltos de linea sueltos
    return texto.strip()


def extraer_paginas(ruta: str, min_caracteres: int = 30) -> list[dict]:
    """Devuelve [{'pagina': 1, 'texto': '...'}, ...] sin paginas vacias."""
    lector = pypdf.PdfReader(ruta)
    paginas = []
    vacias = 0

    for n, pagina in enumerate(lector.pages, start=1):
        texto = limpiar(pagina.extract_text() or "")
        if len(texto) < min_caracteres:
            vacias += 1
            continue
        paginas.append({"pagina": n, "texto": texto})

    if vacias:
        print(f"  aviso: {vacias} paginas con menos de {min_caracteres} "
              f"caracteres fueron descartadas (probablemente imagenes o separadores)")

    return paginas


def resumen(paginas: list[dict]) -> dict:
    """Estadisticas del corpus. Util para el panel y para el informe."""
    caracteres = sum(len(p["texto"]) for p in paginas)
    palabras = sum(len(p["texto"].split()) for p in paginas)
    return {
        "paginas": len(paginas),
        "caracteres": caracteres,
        "palabras": palabras,
        "tokens_estimados": round(caracteres / 3),  # espanol ~3 chars/token
    }
