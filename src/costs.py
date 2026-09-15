"""Contabilidad de tokens y dinero. Lo primero que se escribe en cualquier
proyecto con LLM: sin esto no puedes explicar la factura ni optimizar nada.
"""

from __future__ import annotations
import csv
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

CAMPOS = ["ts", "modelo", "operacion", "tokens_in", "tokens_in_cache",
          "tokens_out", "costo_usd", "latencia_s", "exito", "error"]


@dataclass
class Registro:
    ts: str
    modelo: str
    operacion: str
    tokens_in: int = 0
    tokens_in_cache: int = 0
    tokens_out: int = 0
    costo_usd: float = 0.0
    latencia_s: float = 0.0
    exito: bool = True
    error: str = ""


def costo_usd(precios: dict, modelo: str, tok_in: int, tok_out: int,
              tok_in_cache: int = 0) -> float:
    """Costo de una llamada.

        costo_in  = (tokens_in  / 1_000_000) * precio_in
        costo_out = (tokens_out / 1_000_000) * precio_out
        total     = costo_in + costo_out

    Los tokens que entran por cache se cobran a su propia tarifa, mucho
    menor. DeepSeek los reporta por separado en el objeto usage.
    """
    p = precios["modelos"].get(modelo)
    if p is None:
        return 0.0
    p_cache = p.get("in_cache", p["in"] * 0.1)
    frescos = max(tok_in - tok_in_cache, 0)
    return (frescos / 1e6) * p["in"] \
         + (tok_in_cache / 1e6) * p_cache \
         + (tok_out / 1e6) * p["out"]


class Contador:
    """Acumula registros en memoria y los persiste en CSV por append."""

    def __init__(self, ruta: str):
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.registros: list[Registro] = []
        if not self.ruta.exists():
            with self.ruta.open("w", newline="", encoding="utf-8") as f:
                csv.DictWriter(f, fieldnames=CAMPOS).writeheader()

    def registrar(self, **kw) -> Registro:
        r = Registro(ts=datetime.now().isoformat(timespec="seconds"), **kw)
        self.registros.append(r)
        with self.ruta.open("a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=CAMPOS).writerow(asdict(r))
        return r

    def totales(self) -> dict:
        if not self.registros:
            return {"llamadas": 0, "tokens_in": 0, "tokens_out": 0,
                    "costo_usd": 0.0, "latencia_media": 0.0}
        n = len(self.registros)
        return {
            "llamadas": n,
            "tokens_in": sum(r.tokens_in for r in self.registros),
            "tokens_out": sum(r.tokens_out for r in self.registros),
            "costo_usd": round(sum(r.costo_usd for r in self.registros), 6),
            "latencia_media": round(sum(r.latencia_s for r in self.registros) / n, 2),
        }


def reporte(ruta: str):
    """Agrega el CSV historico por modelo y operacion."""
    import pandas as pd
    df = pd.read_csv(ruta)
    if df.empty:
        print("sin registros")
        return df
    return (df.groupby(["modelo", "operacion"])
              .agg(llamadas=("costo_usd", "size"),
                   tokens_in=("tokens_in", "sum"),
                   tokens_out=("tokens_out", "sum"),
                   costo_usd=("costo_usd", "sum"),
                   latencia_media=("latencia_s", "mean"),
                   tasa_exito=("exito", "mean"))
              .round(6))


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src import settings
    print(reporte(settings.cargar()["logs"]["costos"]))
