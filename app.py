from google import genai
from google.genai.errors import APIError
from PIL import Image
import streamlit as st

# 1. Configuração da página do Streamlit
st.set_page_config(
    page_title="Leitor de Relógio - Água e Gás", page_icon="💧", layout="centered"
)

st.title("💧🔥 Leitor Inteligente de Relógio (Água e Gás)")
st.write(
    "Envie ou tire uma foto do hidrômetro (água) ou do medidor de gás para o"
    " Gemini extrair a leitura atual automaticamente."
)


# 2. Inicialização do Cliente do Google GenAI
@st.cache_resource
def get_genai_client():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("⚠️ Chave GOOGLE_API_KEY não encontrada nos Secrets!")
        st.stop()
    return genai.Client(api_key=api_key)


try:
    client = get_genai_client()
except Exception as e:
    st.error(f"Erro ao inicializar o cliente: {e}")
    st.stop()


# 3. Escolha do tipo de medidor
tipo_medidor = st.radio(
    "Selecione o tipo de medidor:",
    ["Água (Hidrômetro)", "Gás"],
    horizontal=True,
)

# 4. Upload da foto do relógio
uploaded_file = st.file_uploader(
    "Envie a foto do relógio:", type=["png", "jpg", "jpeg"]
)

if uploaded_file is not None:
    # Exibe a imagem na tela
    imagem = Image.open(uploaded_file)
    st.image(
        imagem, caption="Foto do medidor enviada", use_container_width=True
    )

    if st.button("🔍 Ler Medição", type="primary"):
        with st.spinner(
            "Analisando os números do relógio com o Gemini..."
        ):
            try:
                # Define o prompt especializado dependendo do tipo
                if "Água" in tipo_medidor:
                    prompt = (
                        "Analise esta imagem de um hidrômetro (relógio de água)."
                        " Identifique e retorne claramente o número da leitura"
                        " atual exibido nos ponteiros ou no visor digital."
                        " Ignore decimais muito pequenos se necessário, mas"
                        " informe os números principais com precisão."
                    )
                else:
                    prompt = (
                        "Analise esta imagem de um medidor de gás. Identifique"
                        " e retorne claramente o número da leitura atual"
                        " exibido no visor."
                    )

                # Chamada usando a nova SDK google-genai
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=[imagem, prompt]
                )

                # Exibe o resultado da leitura
                st.success("Leitura concluída!")
                st.markdown("### Resultado:")
                st.write(response.text)

            except APIError as api_err:
                st.error(f"Erro na API do Gemini: {api_err.message}")
            except Exception as ex:
                st.error(f"Ocorreu um erro inesperado: {ex}")
