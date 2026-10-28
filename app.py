import os
from google import genai
from google.genai.errors import APIError
import pandas as pd
from PIL import Image
import streamlit as st

# 1. Configuração da página do Streamlit
st.set_page_config(
    page_title="Gemini AI App", page_icon="🤖", layout="wide"
)

st.title("🤖 Assistente Gemini")


# 2. Inicialização do Cliente do Google GenAI
@st.cache_resource
def get_genai_client():
    # Tenta carregar a chave dos Secrets do Streamlit ou do ambiente
    api_key = st.secrets.get("GOOGLE_API_KEY") or os.environ.get(
        "GOOGLE_API_KEY"
    )

    if not api_key:
        st.error(
            "⚠️ Chave de API não encontrada! Configure GOOGLE_API_KEY nos Secrets do Streamlit."
        )
        st.stop()

    # Inicializa o cliente oficial google-genai
    return genai.Client(api_key=api_key)


try:
    client = get_genai_client()
except Exception as e:
    st.error(f"Erro ao inicializar o cliente da API: {e}")
    st.stop()


# 3. Sidebar para seleções e upload de arquivos
st.sidebar.header("Configurações")

# Seleção do Modelo
model_option = st.sidebar.selectbox(
    "Escolha o modelo:",
    ["gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
    index=0,
)

# Upload de Imagem (opcional)
uploaded_image = st.sidebar.file_uploader(
    "Envie uma imagem (opcional)", type=["png", "jpg", "jpeg"]
)

# Upload de Planilha (opcional)
uploaded_excel = st.sidebar.file_uploader(
    "Envie uma planilha Excel/CSV (opcional)", type=["xlsx", "xls", "csv"]
)


# 4. Processamento dos arquivos anexados
image_input = None
if uploaded_image:
    image_input = Image.open(uploaded_image)
    st.sidebar.image(
        image_input, caption="Imagem carregada", use_container_width=True
    )

excel_context = ""
if uploaded_excel:
    try:
        if uploaded_excel.name.endswith(".csv"):
            df = pd.read_csv(uploaded_excel)
        else:
            df = pd.read_excel(uploaded_excel)

        st.subheader("Pré-visualização da Planilha")
        st.dataframe(df.head())

        # Converte as primeiras linhas em texto para dar contexto ao modelo
        excel_context = f"\n\nConteúdo/Amostra dos dados da planilha:\n{df.head(20).to_string()}"
    except Exception as e:
        st.sidebar.error(f"Erro ao ler a planilha: {e}")


# 5. Área de entrada do usuário e geração
prompt_input = st.text_area(
    "Digite sua pergunta ou instrução:",
    height=120,
    placeholder="Ex: Analise esta imagem / Faça um resumo dos dados...",
)

if st.button("Enviar", type="primary"):
    if not prompt_input.strip() and not image_input:
        st.warning("Por favor, digite um texto ou envie uma imagem.")
    else:
        with st.spinner("Processando solicitação com o Gemini..."):
            try:
                # Prepara o conteúdo a ser enviado
                contents = []

                if image_input:
                    contents.append(image_input)

                # Combina o texto do usuário com os dados da planilha (se houver)
                full_text_prompt = prompt_input + excel_context
                contents.append(full_text_prompt)

                # Chamada oficial da biblioteca google-genai
                response = client.models.generate_content(
                    model=model_option, contents=contents
                )

                # Exibe a resposta
                st.markdown("### Resposta:")
                st.write(response.text)

            except APIError as api_err:
                st.error(f"Erro na API do Google Gemini: {api_err.message}")
            except Exception as ex:
                st.error(f"Ocorreu um erro inesperado: {ex}")
