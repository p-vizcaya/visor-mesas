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

@st.cache_data
def download_file():
    if not os.path.exists(LOCAL_FILE):
        url = f"https://drive.google.com/uc?id={FILE_ID}"
        gdown.download(url, LOCAL_FILE, quiet=False)
    return LOCAL_FILE

@st.cache_data
def load_data():
    archivo = download_file()

    df = pd.read_csv(
        archivo,
        usecols=lambda c: c in cols,
        dtype="string",
        encoding="utf-8",
        keep_default_na=False
    )

    for col in df.columns:
        df[col] = (
            df[col]
            .astype("string")
            .str.strip()
            .str.replace('"', '', regex=False)
        )

    df["votos"] = pd.to_numeric(df["votos"], errors="coerce").fillna(0).astype("int32")

    return df

df = load_data()

st.title("Consulta de resultados por mesa")

mesas = sorted(df["id_mesa"].dropna().unique())

mesa = st.selectbox("Seleccione una mesa", mesas)

res = df[df["id_mesa"] == mesa]

resumen = (
    res.groupby(["nom_candi", "nombre_partido"], as_index=False)["votos"]
    .sum()
    .sort_values("votos", ascending=False)
)

st.subheader(f"Resultados para mesa {mesa}")
st.dataframe(resumen, width="stretch")
st.metric("Total votos", int(resumen["votos"].sum()))
