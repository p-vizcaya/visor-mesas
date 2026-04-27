import streamlit as st
import pandas as pd

archivo = "base_camara_preconteo_2026.csv"

cols = [
    "id_mesa",
    "nom_candi",
    "nombre_partido",
    "votos",
    "nombre_departamento",
    "nombre_municipio",
    "nombre_puesto"
]

# Carga de datos
@st.cache_data
def load_data():
    df = pd.read_csv(
        archivo,
        usecols=lambda c: c in cols,
        dtype="string",
        encoding="utf-8",
        keep_default_na=False
    )

    # Limpieza
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

# UI
st.title("Consulta de resultados por mesa")

# Selector
mesas = sorted(df["id_mesa"].dropna().unique())

mesa = st.selectbox(
    "Seleccione una mesa",
    mesas
)

# Filtrado
res = df[df["id_mesa"] == mesa]

# Agrupación
resumen = (
    res.groupby(["nom_candi", "nombre_partido"], as_index=False)["votos"]
    .sum()
    .sort_values("votos", ascending=False)
)

# Visualización
st.subheader(f"Resultados para mesa {mesa}")

st.dataframe(
    resumen,
    width="stretch"
)

st.metric("Total votos", int(resumen["votos"].sum()))