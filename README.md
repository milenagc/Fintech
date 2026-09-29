# Fintech 

Dashboard de Ciência de Dados para tratamento, análise e detecção de anomalias em transações financeiras.

## Objetivo

A aplicação implementa um pipeline completo para:

- ingestão de `transacoes.csv` e `cotacoes.csv`;
- leitura de `transacoes.csv` com encoding legado `latin1`;
- tratamento de valores ausentes pela mediana por estado;
- deduplicação;
- criação da coluna `plataforma = "Mobile"`;
- conversão temporal para `datetime64[ns]` com timezone `America/Sao_Paulo`;
- criação de dia da semana e mês usando `.dt`;
- filtro vetorizado com `&` e `|`;
- classificação de risco usando `.map()`;
- `pivot_table()` com `margins=True`;
- detecção de anomalias por Z-Score sem loops sobre os registros;
- gráfico de valor diário e média móvel de 7 dias usando a API orientada a objetos do Matplotlib.

## Estrutura

```text
Fintech/
├── app.py
├── gerar_dados.py
├── requirements.txt
├── README.md
└── .gitignore
```

## 1. Criar ambiente virtual

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2. Instalar dependências

```bash
pip install -r requirements.txt
```

## 3. Gerar os dados de exemplo

```bash
python gerar_dados.py
```

Serão criados:

```text
transacoes.csv
cotacoes.csv
```

## 4. Executar o dashboard

```bash
streamlit run app.py
```

O Streamlit abrirá o dashboard no navegador.

## Implementação dos requisitos

### Imputação por mediana

```python
medianas = df.groupby("estado_cliente")["valor"].transform("median")
df["valor"] = df["valor"].fillna(medianas)
```

### Timezone

```python
df["data_transacao"] = pd.to_datetime(df["data_transacao"])
df["data_transacao"] = df["data_transacao"].dt.tz_localize(
    "America/Sao_Paulo"
)
```

### Filtro vetorizado

O filtro usa explicitamente os operadores bitwise:

```python
filtro = (
    ((df["estado_cliente"] == "SP") | (df["estado_cliente"] == "RJ"))
    & (df["mes"] == 9)
    & (df["valor"] > 5000)
)
```

### Mapeamento de risco

```python
df["nivel_risco"] = df["id_cliente"].map(RISCO_DICT)
```

### Pivot table

```python
pd.pivot_table(
    df,
    index="mes",
    columns="nivel_risco",
    values="valor",
    aggfunc="sum",
    margins=True,
)
```

### Z-Score vetorizado

```python
grupo = df.groupby("estado_cliente")["valor"]
media = grupo.transform("mean")
desvio = grupo.transform("std")

df["z_score"] = (df["valor"] - media) / desvio
anomalias = df[df["z_score"] > 2.5]
```

### Média móvel

```python
diario["media_movel_7d"] = diario["valor_total"].rolling(7).mean()
```

### Visualização OO com Matplotlib

```python
fig, ax = plt.subplots()

ax.plot(...)
ax.plot(...)

ax.set_ylim(bottom=0)
ax.set_title(...)
ax.legend()
```

## Observação sobre o Z-Score

A implementação usa o desvio-padrão amostral do Pandas (`std`, `ddof=1`), enquanto a fórmula conceitual do exercício apresenta `σ` de forma genérica. O importante para a regra solicitada é calcular o Z-Score por estado de maneira vetorizada e selecionar `Z > 2.5`.

## Tecnologias

- Python
- Pandas
- NumPy
- Matplotlib
- Streamlit

## Possíveis extensões

- cruzar transações com `cotacoes.csv` por data;
- adicionar evolução da cotação USD;
- criar alertas automáticos de fraude;
- persistir resultados em banco de dados;
- adicionar testes automatizados;
- publicar o dashboard em Streamlit Community Cloud.
