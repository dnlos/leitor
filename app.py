import pandas as pd
from google import genai
from PIL import Image
import streamlit as st

# Configuração da página
st.set_page_config(page_title="Leitor de Medidores", page_icon="⚡")

st.title("📊 Leitor de Medidores (Água e Gás)")
st.write(
    "Tire ou envie a foto do medidor para extrair as leituras automaticamente."
)

# Inicializa o cliente Gemini (certifique-se de configurar o secret ou variável de ambiente)
client = genai.Client()

# Seleção do tipo de medidor
tipo = st.selectbox("Selecione o tipo de medição:", ["Água", "Gás"])

# Wiadget para tirar foto direto da câmera do celular ou carregar arquivo
arquivo_foto = st.camera_input("Tirar foto do medidor")
# Ou se preferir galeria: arquivo_foto = st.file_uploader("Escolha a imagem", type=["jpg", "jpeg", "png"])

if arquivo_foto is not None:
  imagem = Image.open(arquivo_foto)
  st.image(
      imagem, caption="Foto enviada", use_column_width=True
  )  # Corrigido para use_container_width em versões mais novas se necessário

  if st.button("Processar Leitura"):
    with st.spinner("Lendo os medidores com IA..."):
      prompt = f"""
            Esta é uma foto de medidores de {tipo} de um condomínio.
            A imagem mostra os números dos apartamentos etiquetados e os mostradores dos relógios correspondentes.
            
            Analise a imagem e retorne APENAS um JSON válido contendo uma lista de registros. 
            Cada registro deve ter:
            - "apartamento": o número do apartamento (ex: "1001", "1002", etc.)
            - "leitura": os números exibidos no visor mecânico do relógio correspondente.
            
            Exemplo:
            [
              {{"apartamento": "1001", "leitura": "001626"}},
              {{"apartamento": "1002", "leitura": "000003"}}
            ]
            Retorne estritamente o JSON válido.
            """

      response = client.models.generate_content(
          model="gemini-2.5-flash", contents=[imagem, prompt]
      )

      texto_resposta = response.text.strip()
      if texto_resposta.startswith("```json"):
        texto_resposta = (
            texto_resposta.removeprefix("```json").removesuffix("```").strip()
        )
      elif texto_resposta.startswith("```"):
        texto_resposta = (
            texto_resposta.removeprefix("```").removesuffix("```").strip()
        )

      import json

      try:
        dados = json.loads(texto_resposta)
        st.success("Leitura realizada com sucesso!")

        # Exibe em tabela na tela
        df = pd.DataFrame(dados)
        st.dataframe(df)

        # Botão para baixar em Excel
        @st.cache_data
        def converter_excel(df):
          output = io.BytesIO()
          with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Leituras")
          return output.getvalue()

        import io

        excel_data = converter_excel(df)

        st.download_button(
            label="📥 Baixar Planilha Atualizada (.xlsx)",
            data=excel_data,
            file_name=f"leituras_{tipo.lower()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

      except Exception as e:
        st.error(f"Erro ao interpretar o retorno da IA: {e}")
        st.text(texto_resposta)
