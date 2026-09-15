"""Interfaz Streamlit. Es un ADAPTADOR: no contiene logica de RAG.

    streamlit run app.py

Los controles del panel no son decoracion: son instrumentos. Mover k o
temperature y ver como cambian la respuesta, el costo y la similitud es
exactamente lo que queremos que el alumno experimente.
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from src import settings, rag_core

st.set_page_config(page_title="Chatbot Beca 18", layout="wide")


@st.cache_resource
def cargar_motor():
    return rag_core.MotorRAG()


cfg = settings.cargar()

st.title("Chatbot normativo Beca 18")
st.caption(cfg["documento"]["nombre"] + " - " + cfg["documento"]["descripcion"])

# ---- estado de sesion: el medidor acumulado -------------------------------
if "acumulado" not in st.session_state:
    st.session_state.acumulado = {"consultas": 0, "tokens_in": 0,
                                  "tokens_out": 0, "costo": 0.0}

# ---- barra lateral: los instrumentos --------------------------------------
with st.sidebar:
    st.header("Parametros")
    k = st.slider("k  (fragmentos recuperados)", 1, 15, cfg["generacion"]["k"])
    temperature = st.slider("temperature", 0.0, 1.5,
                            cfg["generacion"]["temperature"], 0.1)
    modelo = st.selectbox("Modelo", list(cfg["precios"]["modelos"].keys()))

    st.divider()
    st.header("Corpus")
    try:
        info = cargar_motor().info_corpus()
        st.metric("Fragmentos indexados", info["fragmentos_indexados"])
        st.caption(f"Embeddings: {info['modelo_embeddings']}")
        st.caption(f"Dimensiones: {info['dimensiones']}")
    except Exception as e:
        st.error(str(e))

    st.divider()
    st.header("Precios")
    st.caption(f"Verificado el {cfg['precios']['verificado_el']}")
    p = cfg["precios"]["modelos"][modelo]
    st.caption(f"in {p['in']} / out {p['out']} USD por millon")

# ---- medidor acumulado -----------------------------------------------------
a = st.session_state.acumulado
c1, c2, c3, c4 = st.columns(4)
c1.metric("Consultas", a["consultas"])
c2.metric("Tokens entrada", f"{a['tokens_in']:,}")
c3.metric("Tokens salida", f"{a['tokens_out']:,}")
c4.metric("Costo sesion", f"USD {a['costo']:.6f}")

st.divider()

pregunta = st.text_area("Pregunta sobre el reglamento", height=80,
                        placeholder="Ej: cuanto es la subvencion mensual?")
consultar = st.button("Consultar", type="primary")

if consultar and pregunta.strip():
    with st.spinner("Buscando en el reglamento..."):
        r = cargar_motor().responder(pregunta.strip(), k=k,
                                     temperature=temperature, modelo=modelo)

    a["consultas"] += 1
    a["tokens_in"] += r["tokens_in"]
    a["tokens_out"] += r["tokens_out"]
    a["costo"] += r["costo_usd"]

    if r.get("abstuvo"):
        st.warning(r["respuesta"])
        if r.get("motivo"):
            st.caption("Motivo: " + r["motivo"])
    else:
        st.success(r["respuesta"])

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Tokens entrada", r["tokens_in"])
    m2.metric("Tokens salida", r["tokens_out"])
    m3.metric("Costo", f"USD {r['costo_usd']:.8f}")
    m4.metric("Latencia", f"{r['latencia_s']} s")

    with st.expander(f"Ver los {len(r['fuentes'])} fragmentos recuperados"):
        for i, f in enumerate(r["fuentes"], 1):
            st.markdown(
                f"**Fragmento {i}** - pagina **{f['pagina']}** - "
                f"similitud **{f['similitud']}** (distancia {f['distancia']})"
            )
            st.text(f["texto"][:600])
            st.divider()
