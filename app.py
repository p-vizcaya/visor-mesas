import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime
from zoneinfo import ZoneInfo

PROJECT_ID = "elecciones-publico"
TABLE_ID = "`elecciones-publico.DatosElectorales.BaseAppLimpia`"

@st.cache_resource
def get_client():
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"]
    )
    return bigquery.Client(credentials=credentials, project=PROJECT_ID)

def run_query(query, params=None):
    client = get_client()
    job_config = bigquery.QueryJobConfig(query_parameters=params or [])
    return client.query(query, job_config=job_config).to_dataframe()

st.title("Consulta de resultados por mesa")

departamentos = run_query(f"""
    SELECT DISTINCT nombre_departamento
    FROM {TABLE_ID}
    ORDER BY nombre_departamento
""")["nombre_departamento"].tolist()

departamento = st.selectbox("Departamento", departamentos)

municipios = run_query(
    f"""
    SELECT DISTINCT nombre_municipio
    FROM {TABLE_ID}
    WHERE nombre_departamento = @departamento
    ORDER BY nombre_municipio
    """,
    [bigquery.ScalarQueryParameter("departamento", "STRING", departamento)]
)["nombre_municipio"].tolist()

municipio = st.selectbox("Municipio", municipios)

puestos = run_query(
    f"""
    SELECT DISTINCT nombre_puesto
    FROM {TABLE_ID}
    WHERE nombre_departamento = @departamento
      AND nombre_municipio = @municipio
    ORDER BY nombre_puesto
    """,
    [
        bigquery.ScalarQueryParameter("departamento", "STRING", departamento),
        bigquery.ScalarQueryParameter("municipio", "STRING", municipio),
    ],
)["nombre_puesto"].tolist()

puesto = st.selectbox("Puesto", puestos)

mesas = run_query(
    f"""
    SELECT DISTINCT numero_mesa
    FROM {TABLE_ID}
    WHERE nombre_departamento = @departamento
      AND nombre_municipio = @municipio
      AND nombre_puesto = @puesto
    ORDER BY numero_mesa
    """,
    [
        bigquery.ScalarQueryParameter("departamento", "STRING", departamento),
        bigquery.ScalarQueryParameter("municipio", "STRING", municipio),
        bigquery.ScalarQueryParameter("puesto", "STRING", puesto),
    ],
)["numero_mesa"].tolist()

mesa = st.selectbox("Mesa", mesas)

if st.button("Consultar resultados"):
    resultados = run_query(
        f"""
        SELECT
          code_candi,
          nom_candi,
          nombre_partido,
          SUM(votos) AS votos
        FROM {TABLE_ID}
        WHERE nombre_departamento = @departamento
          AND nombre_municipio = @municipio
          AND nombre_puesto = @puesto
          AND numero_mesa = @mesa
        GROUP BY code_candi, nom_candi, nombre_partido
        ORDER BY votos DESC
        """,
        [
            bigquery.ScalarQueryParameter("departamento", "STRING", departamento),
            bigquery.ScalarQueryParameter("municipio", "STRING", municipio),
            bigquery.ScalarQueryParameter("puesto", "STRING", puesto),
            bigquery.ScalarQueryParameter("mesa", "STRING", mesa),
        ],
    )

    total_votos = int(resultados["votos"].sum())

    resultados = resultados.reset_index(drop=True)
    resultados.insert(0, "fila", resultados.index + 1)

    fecha_consulta = datetime.now(ZoneInfo("America/Bogota")).strftime("%Y-%m-%d %H:%M:%S")

    resultados["departamento"] = departamento
    resultados["municipio"] = municipio
    resultados["puesto"] = puesto
    resultados["mesa"] = mesa
    resultados["fecha_consulta"] = fecha_consulta
    resultados["total_votos_mesa"] = total_votos

    columnas_mostrar = ["fila", "code_candi", "nom_candi", "nombre_partido", "votos"]

    columnas_exportar = [
        "fecha_consulta",
        "departamento",
        "municipio",
        "puesto",
        "mesa",
        "total_votos_mesa",
        "fila",
        "code_candi",
        "nom_candi",
        "nombre_partido",
        "votos",
    ]

    st.subheader(f"Resultados mesa {mesa}")
    st.caption(f"Consulta generada: {fecha_consulta} hora Colombia")

    tabla = resultados[columnas_mostrar].style.set_properties(
        subset=["votos"],
        **{"text-align": "center"}
    ).set_table_styles([
        {
            "selector": "th.col_heading.level0.col4",
            "props": [("text-align", "center")]
        }
    ])

    st.dataframe(
        tabla,
        width="stretch",
        hide_index=True
    )

    st.metric("Total votos", total_votos)

    csv = resultados[columnas_exportar].to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="Descargar CSV",
        data=csv,
        file_name=f"resultados_mesa_{mesa}.csv",
        mime="text/csv",
    )
