"""Paso 2 - Partir el texto en fragmentos, conservando el numero de pagina.

Cada chunk sale con su metadato de pagina intacto porque troceamos PAGINA
POR PAGINA en lugar de trocear un texto gigante concatenado.
"""

from __future__ import annotations
from langchain_text_splitters import RecursiveCharacterTextSplitter


def trocear(paginas: list[dict], tamano: int, solape: int,
            separadores: list[str]) -> list[dict]:
    """Devuelve [{'id','texto','pagina'}, ...].

    tamano : caracteres por fragmento
    solape : caracteres repetidos entre fragmentos contiguos, para que una
             frase cortada al final de uno reaparezca al inicio del siguiente
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=tamano,
        chunk_overlap=solape,
        separators=separadores,
    )

    chunks = []
    for p in paginas:
        for pedazo in splitter.split_text(p["texto"]):
            chunks.append({
                "id": f"chunk_{len(chunks):05d}",
                "texto": pedazo,
                "pagina": p["pagina"],
            })
    return chunks


def resumen(chunks: list[dict]) -> dict:
    largos = [len(c["texto"]) for c in chunks]
    return {
        "chunks": len(chunks),
        "largo_promedio": round(sum(largos) / len(largos)) if largos else 0,
        "largo_min": min(largos) if largos else 0,
        "largo_max": max(largos) if largos else 0,
        "paginas_cubiertas": len({c["pagina"] for c in chunks}),
        "con_pagina": sum(1 for c in chunks if c["pagina"]),  # debe ser 100%
    }
