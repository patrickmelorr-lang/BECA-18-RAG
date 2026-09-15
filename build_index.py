"""Proceso OFFLINE. Se corre una vez, antes de la clase.

    python build_index.py

PDF -> paginas -> fragmentos -> vectores -> ChromaDB en disco.
Es idempotente: correrlo dos veces no duplica nada.
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src import settings, extract, chunking, embeddings, index


def main():
    cfg = settings.cargar()
    t0 = time.time()

    print("PASO 1  Extraccion del PDF")
    paginas = extract.extraer_paginas(cfg["documento"]["ruta"])
    r1 = extract.resumen(paginas)
    print(f"  {r1['paginas']} paginas | {r1['caracteres']:,} caracteres | "
          f"~{r1['tokens_estimados']:,} tokens")

    print("\nPASO 2  Chunking pagina por pagina")
    chunks = chunking.trocear(paginas, cfg["chunking"]["tamano"],
                              cfg["chunking"]["solape"],
                              cfg["chunking"]["separadores"])
    r2 = chunking.resumen(chunks)
    print(f"  {r2['chunks']} fragmentos | largo promedio {r2['largo_promedio']} car.")
    print(f"  con numero de pagina: {r2['con_pagina']}/{r2['chunks']} "
          f"({r2['con_pagina']/r2['chunks']*100:.1f}%)")

    print("\nPASO 3  Embeddings locales")
    emb = embeddings.Embebedor(cfg["embeddings"])
    print(f"  dimensiones: {emb.dim}")

    print("\nPASO 4  Indexado en ChromaDB")
    col = index.abrir_coleccion(cfg["indice"])
    n = index.indexar(col, chunks, emb, lote=cfg["embeddings"]["lote"])
    print(f"  fragmentos agregados: {n}")
    print(f"  total en la coleccion: {col.count()}")

    print(f"\nListo en {time.time()-t0:.1f} s. Ahora: streamlit run app.py")


if __name__ == "__main__":
    main()
