"""Paso 4 - Base vectorial ChromaDB: guardar y buscar.

Idempotente: si la coleccion ya tiene los fragmentos, no reindexa.
Reanudable: si se corto a la mitad, continua donde quedo.

Nota importante para clase: Chroma devuelve DISTANCIA, no similitud.
Con metrica 'cosine',  similitud = 1 - distancia.  Mostramos las dos
para que nadie confunda 'numero chico' con 'mal resultado'.
"""

from __future__ import annotations
import chromadb


def abrir_coleccion(cfg_indice: dict):
    cliente = chromadb.PersistentClient(path=cfg_indice["ruta"])
    return cliente.get_or_create_collection(
        name=cfg_indice["coleccion"],
        metadata={"hnsw:space": cfg_indice["metrica"]},
    )


def indexar(coleccion, chunks: list[dict], embebedor, lote: int = 64) -> int:
    """Carga los fragmentos al indice. Devuelve cuantos agrego."""
    ya = coleccion.count()
    if ya >= len(chunks):
        print(f"  indice ya completo: {ya} fragmentos")
        return 0

    if ya > 0:
        print(f"  reanudando desde el fragmento {ya} ({len(chunks) - ya} faltan)")

    agregados = 0
    for i in range(ya, len(chunks), lote):
        bloque = chunks[i:i + lote]
        textos = [c["texto"] for c in bloque]
        coleccion.add(
            ids=[c["id"] for c in bloque],
            documents=textos,
            embeddings=embebedor.documentos(textos),
            metadatas=[{"pagina": c["pagina"]} for c in bloque],
        )
        agregados += len(bloque)
    return agregados


def buscar(coleccion, embebedor, pregunta: str, k: int = 5) -> list[dict]:
    """Top-k fragmentos mas parecidos, con pagina y similitud."""
    res = coleccion.query(
        query_embeddings=[embebedor.consulta(pregunta)],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    salida = []
    for i in range(len(res["documents"][0])):
        distancia = float(res["distances"][0][i])
        salida.append({
            "texto": res["documents"][0][i],
            "pagina": res["metadatas"][0][i].get("pagina"),
            "distancia": round(distancia, 4),
            "similitud": round(1 - distancia, 4),
        })
    return salida
