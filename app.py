import io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Fintech Transaction Intelligence", page_icon="📊", layout="wide")

RISCO_DICT = {
    "C100": "Baixo",
    "C101": "Alto",
    "C102": "Médio",
    "C103": "Baixo",
    "C104": "Alto",
}

@st.cache_data
def carregar_transacoes(upload):
    return pd.read_csv(upload, encoding="latin1")

@st.cache_data
def carregar_cotacoes(upload):
    return pd.read_csv(upload, encoding="utf-8")

def processar_transacoes(df):
    df = df.copy()

    df = df.drop_duplicates(keep="first").copy()

    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    medianas = df.groupby("estado_cliente")["valor"].transform("median")
    df["valor"] = df["valor"].fillna(medianas)

    df["plataforma"] = "Mobile"

    df["data_transacao"] = pd.to_datetime(df["data_transacao"], errors="coerce")
    df["data_transacao"] = df["data_transacao"].dt.tz_localize(
        "America/Sao_Paulo", ambiguous="NaT", nonexistent="NaT"
    )

    df["dia_semana"] = df["data_transacao"].dt.day_name("pt_BR")
    df["mes"] = df["data_transacao"].dt.month
    df["data"] = df["data_transacao"].dt.date


    df["nivel_risco"] = df["id_cliente"].map(RISCO_DICT).fillna("Não mapeado")

    return df

def aplicar_filtro(df):

    filtro = (
        ((df["estado_cliente"] == "SP") | (df["estado_cliente"] == "RJ"))
        & (df["mes"] == 9)
        & (df["valor"] > 5000)
    )
    return df.loc[filtro].copy()

def calcular_zscore_por_estado(df):
    grupo = df.groupby("estado_cliente")["valor"]
    media = grupo.transform("mean")
    desvio = grupo.transform("std").replace(0, np.nan)
    df = df.copy()
    df["z_score"] = ((df["valor"] - media) / desvio).fillna(0)
    return df

def criar_pivot(df):
    return pd.pivot_table(
        df,
        index="mes",
        columns="nivel_risco",
        values="valor",
        aggfunc="sum",
        margins=True,
        margins_name="Total geral",
        fill_value=0,
    )

def criar_grafico(df):
    diario = (
        df.set_index("data_transacao")["valor"]
        .resample("D")
        .sum()
        .rename("valor_total")
        .to_frame()
    )
    diario["media_movel_7d"] = diario["valor_total"].rolling(7).mean()

    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.plot(diario.index, diario["valor_total"], label="Valor total diário", linewidth=2)
    ax.plot(
        diario.index,
        diario["media_movel_7d"],
        label="Média móvel de 7 dias",
        linewidth=2,
    )
    ax.set_ylim(bottom=0)
    ax.set_title("Valor total de transações e média móvel de 7 dias")
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor (R$)")
    ax.legend()
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig

st.title("📊 Fintech Transaction Intelligence")
st.caption(
    "Pipeline de limpeza, engenharia de dados, agregação, detecção de anomalias e visualização."
)

with st.sidebar:
    st.header("Arquivos de entrada")
    tx_file = st.file_uploader(
        "transacoes.csv (latin1)",
        type=["csv"],
        key="tx",
    )
    quote_file = st.file_uploader(
        "cotacoes.csv (UTF-8)",
        type=["csv"],
        key="quotes",
    )
    st.divider()
    st.markdown("**Requisitos implementados**")
    st.markdown(
        """
        - Mediana por estado
        - `latin1`
        - `tz_localize`
        - `.dt`
        - Deduplicação
        - Filtro com `&` e `|`
        - `.map()`
        - `pivot_table(margins=True)`
        - Z-Score vetorizado
        - Média móvel de 7 dias
        """
    )

if tx_file is None:
    st.info("Carregue o arquivo `transacoes.csv` para iniciar a análise.")
    st.stop()

try:
    raw = carregar_transacoes(tx_file)
    df = processar_transacoes(raw)
except Exception as exc:
    st.error(f"Erro ao processar transacoes.csv: {exc}")
    st.stop()

quotes = None
if quote_file is not None:
    try:
        quotes = carregar_cotacoes(quote_file)
    except Exception as exc:
        st.warning(f"cotacoes.csv não pôde ser lido: {exc}")

df_z = calcular_zscore_por_estado(df)
anomalias = df_z.loc[df_z["z_score"] > 2.5].sort_values("z_score", ascending=False)
filtrado = aplicar_filtro(df_z)
pivot = criar_pivot(df)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Transações após limpeza", f"{len(df):,}".replace(",", "."))
col2.metric("Valor total", f"R$ {df['valor'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Filtro SP/RJ > R$ 5 mil", f"{len(filtrado):,}".replace(",", "."))
col4.metric("Anomalias Z > 2,5", f"{len(anomalias):,}".replace(",", "."))

st.subheader("Valor diário e média móvel de 7 dias")
st.pyplot(criar_grafico(df), clear_figure=True, use_container_width=True)

c1, c2 = st.columns(2)

with c1:
    st.subheader("Pivot: mês × nível de risco")
    st.dataframe(
        pivot.style.format("R$ {:,.2f}"),
        use_container_width=True,
    )

with c2:
    st.subheader("Potenciais anomalias / fraude")
    st.dataframe(
        anomalias[
            [
                "id_cliente",
                "data_transacao",
                "estado_cliente",
                "valor",
                "nivel_risco",
                "z_score",
            ]
        ].style.format({"valor": "R$ {:,.2f}", "z_score": "{:.2f}"}),
        use_container_width=True,
    )

st.subheader("Filtro vetorizado — setembro, SP/RJ e valor > R$ 5.000")
st.dataframe(
    filtrado[
        [
            "id_cliente",
            "data_transacao",
            "estado_cliente",
            "valor",
            "origem",
            "nivel_risco",
            "plataforma",
        ]
    ].style.format({"valor": "R$ {:,.2f}"}),
    use_container_width=True,
)

with st.expander("Dados tratados"):
    st.dataframe(df, use_container_width=True)

if quotes is not None:
    st.subheader("Cotações")
    st.caption(f"{len(quotes)} registros carregados de cotacoes.csv.")
    st.dataframe(quotes, use_container_width=True)

csv_saida = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Baixar dados tratados",
    data=csv_saida,
    file_name="transacoes_tratadas.csv",
    mime="text/csv",
)
