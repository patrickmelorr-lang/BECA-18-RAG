"""EL MOTOR. Un solo contrato publico:

    responder(pregunta, k=None) -> dict

Regla de arquitectura, verificable con un grep:
este archivo NO importa streamlit ni nada de Telegram. Si lo hiciera,
las interfaces dejarian de ser intercambiables y nada seria testeable.
"""

from __future__ import annotations
import time

from src import settings, extract, chunking, embeddings, index, costs

SYSTEM_PROMPT = """Eres un asistente experto en el reglamento de Beca 18 de PRONABEC.

REGLAS ESTRICTAS:
1. Responde UNICAMENTE con informacion contenida en el CONTEXTO entregado.
2. Cita siempre la pagina de la que sacaste el dato, en el formato (pag. N).
   El numero de pagina aparece al inicio de cada fragmento del contexto.
3. Si el contexto no contiene la respuesta, responde exactamente:
   "No encuentro eso en el reglamento que tengo cargado."
   No completes con conocimiento general ni supongas.
4. Responde en espanol claro, en maximo 5 oraciones."""

SIN_RESPUESTA = "No encuentro eso en el reglamento que tengo cargado."


class MotorRAG:
    def __init__(self, cfg: dict | None = None):
        self.cfg = cfg or settings.cargar()
        self.embebedor = embeddings.Embebedor(self.cfg["embeddings"])
        self.coleccion = index.abrir_coleccion(self.cfg["indice"])
        self.contador = costs.Contador(self.cfg["logs"]["costos"])
        self._cliente = None

        if self.coleccion.count() == 0:
            raise RuntimeError(
                "El indice esta vacio. Corre primero:  python build_index.py"
            )

    # -- conexion perezosa: no pedimos la llave hasta que hace falta -------
    @property
    def cliente(self):
        if self._cliente is None:
            from openai import OpenAI
            self._cliente = OpenAI(
                api_key=settings.api_key("DEEPSEEK_API_KEY"),
                base_url=self.cfg["generacion"]["base_url"],
            )
        return self._cliente

    # -- armado del prompt -------------------------------------------------
    def _contexto(self, fuentes: list[dict]) -> str:
        return "\n\n".join(
            f"[Fragmento {i+1} | pagina {f['pagina']}]\n{f['texto']}"
            for i, f in enumerate(fuentes)
        )

    # -- el metodo publico -------------------------------------------------
    def responder(self, pregunta: str, k: int | None = None,
                  temperature: float | None = None,
                  modelo: str | None = None) -> dict:
        g = self.cfg["generacion"]
        k = k or g["k"]
        temperature = g["temperature"] if temperature is None else temperature
        modelo = modelo or g["modelo"]

        t0 = time.time()
        fuentes = index.buscar(self.coleccion, self.embebedor, pregunta, k=k)

        base = {"pregunta": pregunta, "fuentes": fuentes, "modelo": modelo,
                "k": k, "temperature": temperature,
                "tokens_in": 0, "tokens_in_cache": 0, "tokens_out": 0,
                "costo_usd": 0.0}

        # Corto circuito: si nada se parece lo suficiente, ni llamamos al LLM.
        # Ahorra dinero y elimina la principal via de invencion.
        mejor = fuentes[0]["similitud"] if fuentes else 0.0
        if mejor < g["umbral_similitud"]:
            return {**base, "respuesta": SIN_RESPUESTA, "abstuvo": True,
                    "motivo": f"similitud maxima {mejor} < umbral {g['umbral_similitud']}",
                    "latencia_s": round(time.time() - t0, 3)}

        prompt = (f"CONTEXTO DEL DOCUMENTO:\n{self._contexto(fuentes)}\n\n"
                  f"PREGUNTA: {pregunta}")

        try:
            r = self.cliente.chat.completions.create(
                model=modelo,
                messages=[{"role": "system", "content": SYSTEM_PROMPT},
                          {"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=g["max_tokens"],
                stream=False,
            )
            texto = r.choices[0].message.content
            u = r.usage
            tok_in = getattr(u, "prompt_tokens", 0)
            tok_out = getattr(u, "completion_tokens", 0)
            tok_cache = getattr(u, "prompt_cache_hit_tokens", 0) or 0
            error = ""
            exito = True
        except Exception as e:
            texto = f"Error al llamar al modelo: {e}"
            tok_in = tok_out = tok_cache = 0
            error = str(e)[:200]
            exito = False

        latencia = round(time.time() - t0, 3)
        costo = costs.costo_usd(self.cfg["precios"], modelo, tok_in, tok_out, tok_cache)

        self.contador.registrar(
            modelo=modelo, operacion="generacion",
            tokens_in=tok_in, tokens_in_cache=tok_cache, tokens_out=tok_out,
            costo_usd=round(costo, 8), latencia_s=latencia,
            exito=exito, error=error,
        )

        return {**base, "respuesta": texto,
                "abstuvo": texto.strip().startswith(SIN_RESPUESTA[:20]),
                "motivo": "", "tokens_in": tok_in, "tokens_in_cache": tok_cache,
                "tokens_out": tok_out, "costo_usd": round(costo, 8),
                "latencia_s": latencia, "exito": exito}

    def info_corpus(self) -> dict:
        return {"fragmentos_indexados": self.coleccion.count(),
                "modelo_embeddings": self.cfg["embeddings"]["modelo"],
                "dimensiones": self.embebedor.dim,
                "documento": self.cfg["documento"]["nombre"]}


_motor = None


def motor() -> MotorRAG:
    """Instancia unica, para no recargar el modelo en cada pregunta."""
    global _motor
    if _motor is None:
        _motor = MotorRAG()
    return _motor


def responder(pregunta: str, **kw) -> dict:
    return motor().responder(pregunta, **kw)
