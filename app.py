from datetime import datetime
from google import genai
from google.genai.errors import APIError
import pandas as pd
from PIL import Image
import streamlit as st

# 1. Configuração da página do Streamlit
st.set_page_config(
    page_title="Leitor de Medidores para Planilha", page_icon="📊", layout="wide"
)

st.title("📊 Leitor de Água/Gás e Automação de Planilha")
st.write(
    "Tire ou envie a foto do relógio, o Gemini lê o número e monta os dados"
    " para salvar na planilha."
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


# 3. Layout em colunas (Foto/Leitura de um lado, Planilha/Histórico do outro)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📷 Enviar Foto do Medidor")

    tipo_medidor = st.selectbox(
        "Qual medidor você está lindo?", ["Água (Hidrômetro)", "Gás"]
    )

    # Permite tirar foto direto pela câmera (ótimo para celular) ou carregar arquivo
    camera_ou_arquivo = st.radio(
        "Como deseja enviar a foto?", ["Carregar arquivo", "Usar Câmera"]
    )

    uploaded_file = None
    if camera_ou_arquivo == "Carregar arquivo":
        uploaded_file = st.file_uploader(
            "Escolha a imagem...", type=["png", "jpg", "jpeg"]
        )
    else:
        uploaded_file = st.camera_input("Tire a foto do relógio")

    leitura_extraida = ""

    if uploaded_file is not None:
        imagem = Image.open(uploaded_file)
        st.image(imagem, caption="Medidor capturado", use_container_width=True)

        if st.button("🔍 Ler Número com Gemini", type="primary"):
            with st.spinner("Analisando o visor do relógio..."):
                try:
                    prompt = (
                        f"Analise esta imagem de um medidor de {tipo_medidor}."
                        " Identifique estritamente e retorne apenas o número da"
                        " leitura atual exibido no visor ou ponteiros principais,"
                        " sem textos longos."
                    )

                    response = client.models.generate_content(
                        model="gemini-2.5-flash", contents=[imagem, prompt]
                    )

                    leitura_extraida = response.text.strip()
                    st.success("Leitura realizada com sucesso!")
                    st.metric(
                        label="Número Identificado", value=leitura_extraida
                    )

                except APIError as api_err:
                    st.error(f"Erro na API do Gemini: {api_err.message}")
                except Exception as ex:
                    st.error(f"Erro inesperado: {ex}")

with col2:
    st.subheader("📋 Montar / Atualizar Planilha")

    # Área para registrar o número lido na planilha
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M")

    with st.form("form_planilha"):
        input_tipo = st.text_input("Tipo de Medidor", value=tipo_medidor)
        input_leitura = st.text_input(
            "Leitura Capturada", value=leitura_extraida
        )
        input_data = st.text_input("Data e Hora", value=data_atual)
        input_obs = st.text_area("Observações (ex: Mês de referência)")

        submitted = st.form_submit_button("➕ Adicionar à Tabela")

        if submitted:
            if not input_leitura:
                st.warning(
                    "A leitura está vazia. Faça a leitura da foto primeiro!"
                )
            else:
                # Se já existir um histórico na sessão, adiciona; senão cria um novo
                if "dados_planilha" not in st.session_state:
                    st.session_state["dados_planilha"] = pd.DataFrame(
                        columns=["Data/Hora", "Medidor", "Leitura", "Obs"]
                    )

                nova_linha = pd.DataFrame(
                    [
                        {
                            "Data/Hora": input_data,
                            "Medidor": input_tipo,
                            "Leitura": input_leitura,
                            "Obs": input_obs,
                        }
                    ]
                )

                st.session_state["dados_planilha"] = pd.concat(
                    [st.session_state["dados_planilha"], nova_linha],
                    ignore_index=True,
                )
                st.success("Registro adicionado à tabela com sucesso!")

    # Exibe a tabela acumulada
    if (
        "dados_planilha" in st.session_state
        and not st.session_state["dados_planilha"].empty
    ):
        st.markdown("### Histórico na Planilha")
        st.dataframe(st.session_state["dados_planilha"], use_container_width=True)

        # Botão para baixar a planilha em CSV ou Excel
        csv = st.session_state["dados_planilha"].to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Baixar Planilha (CSV)",
            data=csv,
            file_name="leituras_medidores.csv",
            mime="text/csv",
        )
