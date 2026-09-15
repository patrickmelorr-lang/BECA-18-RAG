"""Evaluacion del sistema. Dos metricas, y miden cosas DISTINTAS:

  Recall@k          -> calidad de la BUSQUEDA (chunking + embeddings)
  Tasa de abstencion -> calidad del PROMPT (que no invente)

El diagnostico que separa a quien entiende RAG de quien copio un tutorial:
si Recall@3 es bajo, el problema es el chunking, NO el LLM. Cambiar de
modelo generador no arregla una busqueda mala.

    python eval/run_eval.py              # solo recuperacion, gratis
    python eval/run_eval.py --generar    # ademas prueba la abstencion (cuesta)
"""
import sys, csv, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import settings, embeddings, index, rag_core

AQUI = Path(__file__).resolve().parent


def cargar_casos():
    with open(AQUI / "preguntas.csv", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def evaluar_recuperacion(casos, ks=(1, 3, 5)):
    """Solo necesita embeddings locales: se puede correr infinitas veces gratis."""
    cfg = settings.cargar()
    emb = embeddings.Embebedor(cfg["embeddings"])
    col = index.abrir_coleccion(cfg["indice"])

    dominio = [c for c in casos if c["tipo"] == "dominio"]
    resultados = {}

    for k in ks:
        aciertos, detalle = 0, []
        for c in dominio:
            esperadas = {int(x) for x in c["paginas_esperadas"].split("|") if x}
            recuperadas = {f["pagina"] for f in
                           index.buscar(col, emb, c["pregunta"], k=k)}
            ok = bool(esperadas & recuperadas)
            aciertos += ok
            detalle.append((c["pregunta"][:50], sorted(recuperadas), ok))
        resultados[k] = aciertos / len(dominio)
        print(f"\nRecall@{k} = {resultados[k]:.2f}  ({aciertos}/{len(dominio)})")
        for preg, rec, ok in detalle:
            print(f"   {'OK ' if ok else 'NO '} {preg:<52} paginas {rec}")
    return resultados


def evaluar_abstencion(casos):
    """Cuesta dinero: una llamada al LLM por cada pregunta fuera de dominio."""
    fuera = [c for c in casos if c["tipo"] == "fuera_de_dominio"]
    motor = rag_core.MotorRAG()
    correctas = 0
    for c in fuera:
        r = motor.responder(c["pregunta"])
        ok = bool(r.get("abstuvo"))
        correctas += ok
        print(f"   {'OK ' if ok else 'FALLA'} {c['pregunta'][:50]:<52} "
              f"-> {r['respuesta'][:60]}")
    tasa = correctas / len(fuera)
    print(f"\nTasa de abstencion correcta = {tasa:.2f} ({correctas}/{len(fuera)})")
    return tasa


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--generar", action="store_true",
                    help="probar tambien la abstencion (consume API)")
    args = ap.parse_args()

    casos = cargar_casos()
    print(f"Casos: {len(casos)}  "
          f"({sum(1 for c in casos if c['tipo']=='dominio')} de dominio, "
          f"{sum(1 for c in casos if c['tipo']=='fuera_de_dominio')} fuera)")

    evaluar_recuperacion(casos)
    if args.generar:
        print("\n--- Abstencion ---")
        evaluar_abstencion(casos)
