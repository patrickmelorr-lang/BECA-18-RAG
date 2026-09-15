"""Paso 3 - Embeddings LOCALES. Sin API, sin costo, sin rate limits.

Reemplaza gemini-embedding-001. El modelo se descarga una sola vez y queda
en cache. Indexar 570 fragmentos pasa de ~15 minutos (con sleep(30) entre
lotes por los limites del free tier) a decenas de segundos en CPU.

Los prefijos 'query: ' y 'passage: ' son el equivalente local del
task_type RETRIEVAL_QUERY / RETRIEVAL_DOCUMENT de Gemini: la familia E5
distingue pregunta de pasaje mediante el texto, no mediante un parametro.
Omitirlos degrada la recuperacion sin que se note por que.
"""

from __future__ import annotations
import numpy as np


class Embebedor:
    def __init__(self, cfg_emb: dict):
        from sentence_transformers import SentenceTransformer
        self.cfg = cfg_emb
        print(f"  cargando modelo de embeddings: {cfg_emb['modelo']}")
        self.modelo = SentenceTransformer(cfg_emb["modelo"])
        self.dim = self.modelo.get_sentence_embedding_dimension()

    def _codificar(self, textos: list[str], prefijo: str) -> list[list[float]]:
        entradas = [prefijo + t for t in textos]
        vectores = self.modelo.encode(
            entradas,
            batch_size=self.cfg["lote"],
            normalize_embeddings=self.cfg["normalizar"],
            show_progress_bar=len(entradas) > 200,
        )
        return np.asarray(vectores, dtype=float).tolist()

    def documentos(self, textos: list[str]) -> list[list[float]]:
        """Vectores para los fragmentos del corpus."""
        return self._codificar(textos, self.cfg["prefijo_documento"])

    def consulta(self, texto: str) -> list[float]:
        """Vector para la pregunta del usuario."""
        return self._codificar([texto], self.cfg["prefijo_consulta"])[0]
