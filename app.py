import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders


@st.cache_data(max_entries=3000, ttl=3600)
def load_data_moedas():
    df = pd.read_csv('BTCUSD_1m_Binance.csv')
    df.rename(columns={
        'Open time': 'Tempo de Abertura',
        'Open': 'Abertura',
        'High': 'Máxima',
        'Low': 'Mínima',
        'Close': 'Fechamento',
        'Quote asset volume': 'Volume de Ativos Cotados',
        'Number of trades': 'Número de Negócios',
        'Taker buy base asset volume': 'Volume de Ativos Comprados pelo Taker (Base)',
        'Taker buy quote asset volume': 'Volume de Ativos Comprados pelo Taker (Cotação)',
        'Ignore': 'Ignorar'
    }, inplace=True)
    return df

@st.cache_data(max_entries=1000, ttl=3600)
def load_robo():
    df = pd.read_excel('ROBO_correto.xlsx')
    return df

@st.cache_data(max_entries=3000, ttl=3600)
def load_data_jogos():
    df = pd.read_csv('vgsales.csv')
    df.rename(columns={
        'Rank': 'Ranking',
        'Name': 'Nome do Jogo',
        'Platform': 'Plataforma',
        'Year': 'Ano de Lançamento',
        'Genre': 'Gênero',
        'Publisher': 'Publicadora',
        'NA_Sales': 'Vendas na América do Norte (milhões)',
        'EU_Sales': 'Vendas na Europa (milhões)',
        'JP_Sales': 'Vendas no Japão (milhões)',
        'Other_Sales': 'Vendas em Outros Mercados (milhões)',
        'Global_Sales': 'Vendas Globais (milhões)'
    }, inplace=True)
    return df

dataset_opcao = st.sidebar.selectbox("Escolha o relatorio", ("Moedas", "Jogos","Redes"))

if dataset_opcao == "Moedas":
    dados = load_data_moedas()
    st.title("Análise de Moedas: BTC/USD")
    st.subheader("Prévia do Dataset")
    st.dataframe(dados.head(5))

elif dataset_opcao == "Jogos":
    dados = load_data_jogos()
    st.title("Análise de Dados: Jogos de Videogame")
    st.subheader("Prévia do Dataset")
    st.dataframe(dados.head(5))

elif dataset_opcao == "Redes":
    dados = load_robo()
    st.title("Análise de Dados: Redes")
    st.subheader("Prévia do Dataset")
    st.dataframe(dados.head(5))

st.sidebar.subheader("Filtros")
colunas = st.sidebar.multiselect(
    "Selecione as colunas que deseja visualizar",
    options=dados.columns.tolist(),
    default=dados.columns.tolist()
)
dados_filtrados = dados[colunas]


if dataset_opcao == "Jogos":
    nome_jogo = st.sidebar.selectbox(
        "Selecione um Jogo",
        options=dados_filtrados['Nome do Jogo'].unique(),
        index=0
    )

    plataforma = st.sidebar.multiselect(
        "Selecione a(s) Plataforma(s)",
        options=dados_filtrados['Plataforma'].unique(),
        default=dados_filtrados['Plataforma'].unique()
    )

    dados_filtrados = dados_filtrados[
        (dados_filtrados['Nome do Jogo'] == nome_jogo) &
        (dados_filtrados['Plataforma'].isin(plataforma))
    ]


st.subheader("Dados Filtrados")
st.dataframe(dados_filtrados)


st.subheader("Estatísticas Gerais")
st.write(dados_filtrados.describe())


if dataset_opcao == "Jogos":
    st.subheader(f"Crescimento das Vendas Globais para o Jogo: {nome_jogo}")
    if 'Ano de Lançamento' in dados_filtrados.columns and 'Vendas Globais (milhões)' in dados_filtrados.columns:
        vendas_ano = dados_filtrados.groupby('Ano de Lançamento')['Vendas Globais (milhões)'].sum().reset_index()
        fig, ax = plt.subplots()
        ax.plot(vendas_ano['Ano de Lançamento'], vendas_ano['Vendas Globais (milhões)'], marker='o', linestyle='-')
        ax.set_title(f"Crescimento de Vendas Globais - {nome_jogo}")
        ax.set_xlabel("Ano de Lançamento")
        ax.set_ylabel("Vendas Globais (milhões)")
        st.pyplot(fig)

        # Relatório escrito
        st.subheader("Relatório")
        st.markdown(f"""
        **Relatório de Crescimento de Vendas**  
        O gráfico acima mostra o crescimento das vendas globais do jogo **{nome_jogo}** ao longo dos anos.  
        Observa-se que as vendas apresentaram uma **tendência de crescimento/declínio** em determinados períodos, indicando o impacto de fatores como popularidade, plataforma e região de lançamento.  
        """)
    else:
        st.write("As colunas 'Ano de Lançamento' e 'Vendas Globais (milhões)' não estão disponíveis no filtro atual.")


def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Dados Filtrados')
        writer.close() 
    processed_data = output.getvalue()
    return processed_data


def send_email(subject, body, to_email, attachment):
    from_email = "agmphandre@gmail.com"
    from_password = "Pedro@2217"
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

 
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    
    msg.attach(MIMEText(body, 'plain'))

    # Adicionar anexo
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment)
    encoders.encode_base64(part)
    part.add_header(
        'Content-Disposition',
        f"attachment; filename=relatorio_{nome_jogo}.xlsx"
    )
    msg.attach(part)

    # Parte do código que envia o e-mail
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(from_email, from_password)
        server.sendmail(from_email, to_email, msg.as_string())

# Botão para enviar o relatório por e-mail
if st.button("Enviar relatório por e-mail"):
    destinatario = st.text_input("Digite o e-mail do destinatário")
    if destinatario:
        corpo_email = f"Segue em anexo o relatório do jogo {nome_jogo}."
        excel_data = to_excel(dados_filtrados)
        send_email(
            subject=f"Relatório de Crescimento - {nome_jogo}",
            body=corpo_email,
            to_email=destinatario,
            attachment=excel_data
        )
        st.success(f"E-mail enviado para {destinatario}!")
    else:
        st.error("Por favor, insira um endereço de e-mail.")


if dataset_opcao == "ROBO":
    st.subheader("Análise de Dados do Robo Corretor")

    if 'Data' in dados.columns and 'Preço' in dados.columns:
        st.subheader("Análise de Preços ao Longo do Tempo")
        dados_filtrados['Data'] = pd.to_datetime(dados_filtrados['Data'], errors='coerce')
        fig, ax = plt.subplots()
        ax.plot(dados_filtrados['Data'], dados_filtrados['Preço'], marker='x', linestyle='-', color='b')
        ax.set_title("Preço ao Longo do Tempo - Robo Corretor")
        ax.set_xlabel("Data")
        ax.set_ylabel("Preço")
        st.pyplot(fig)

      
        st.subheader("Correlação entre variáveis numéricas")
        corr = dados_filtrados.corr()
        st.write(corr)

'''Buscando trazer uma ánalise com filtros em várias tabelas e criando um sistemas de envio de e-mail para qualquer pessoa '''
