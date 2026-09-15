"""Carga la configuracion y las credenciales. Un solo punto de entrada."""

from __future__ import annotations
import os
from pathlib import Path
import yaml

RAIZ = Path(__file__).resolve().parent.parent


def cargar(ruta="config.yaml") -> dict:
    """Lee config.yaml y devuelve un diccionario con las rutas ya absolutas."""
    p = Path(ruta)
    p = p if p.is_absolute() else RAIZ / p
    with open(p, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    cfg["documento"]["ruta"] = str(RAIZ / cfg["documento"]["ruta"])
    cfg["indice"]["ruta"] = str(RAIZ / cfg["indice"]["ruta"])
    cfg["logs"]["costos"] = str(RAIZ / cfg["logs"]["costos"])
    return cfg


def api_key(nombre: str = "DEEPSEEK_API_KEY") -> str:
    """Busca la llave en Colab Secrets, luego en el entorno, luego en .env."""
    try:
        from google.colab import userdata
        valor = userdata.get(nombre)
        if valor:
            return valor
    except Exception:
        pass

    valor = os.getenv(nombre)
    if valor:
        return valor

    try:
        from dotenv import load_dotenv
        load_dotenv(RAIZ / ".env")
        valor = os.getenv(nombre)
    except ImportError:
        pass

    if not valor:
        raise RuntimeError(
            f"No encuentro {nombre}. Ponla en .env, en el entorno "
            f"o en Colab Secrets. Nunca dentro del codigo."
        )
    return valor
