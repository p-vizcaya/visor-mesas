import streamlit as st
import pandas as pd
import gdown
import os

FILE_ID = "11lWEo9_-EnK1bV--LrfYgQT2VqF3HHc1"
LOCAL_FILE = "base_camara_preconteo_2026.csv"

cols = [
    "id_mesa",
    "nom_candi",
    "nombre_partido",
    "votos",
    "nombre_departamento",
    "nombre_municipio",
    "nombre_puesto"
]

@st.cache_data(show_spinner=True)
def download_file():
    if not os.path.exists(LOCAL_FILE):
        url = f"https://drive.google.com/uc?id={FILE_ID}"
        gdown.download(url, LOCAL_FILE, quiet=False)
    return LOCAL_FILE

def limpiar_id(s):
    return str(s).strip().replace('"', '').replace("'", "")

def buscar_mesa(id_mesa):
    archivo = download_file()
    mesa_limpia = limpiar_id(id_mesa)

    partes = []

    for chunk in pd.read_csv(
        archivo,
        usecols=lambda c: c in cols,
        dtype="string",
        encoding="utf-8",
        keep_default_na=False,
        chunksize=200_000
    ):
        chunk["id_mesa"] = chunk["id_mesa"].str.strip().str.replace('"', '', regex=False)

        filtro = chunk[chunk["id_mesa"] == mesa_limpia]

        if not filtro.empty:
            partes.append(filtro)

    if partes:
        return pd.concat(partes, ignore_index=True)

    return pd.DataFrame(columns=cols)

# UI
st.title("Consulta de resultados por mesa")

mesa = st.text_input("Ingrese el ID de la mesa", "")

if st.button("Consultar"):
    with st.spinner("Buscando mesa..."):
        res = buscar_mesa(mesa)

    if res.empty:
        st.warning("No se encontraron resultados.")
    else:
        res["votos"] = pd.to_numeric(res["votos"], errors="coerce").fillna(0).astype("int32")

        resumen = (
            res.groupby(["nom_candi", "nombre_partido"], as_index=False)["votos"]
            .sum()
            .sort_values("votos", ascending=False)
        )

        st.subheader(f"Resultados para mesa {mesa}")
        st.dataframe(resumen, width="stretch")
        st.metric("Total votos", int(resumen["votos"].sum()))
