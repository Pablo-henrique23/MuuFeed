"""MuuFeed — entrada da aplicação. Execute:  streamlit run app.py"""
import streamlit as st

from services.formulation_service import formulador_conectado
from ui import pages
from ui.state import PAGINAS, iniciar_estado
from ui.theme import aplicar_tema

try:
    import pyarrow  # noqa: F401  (necessário para tabelas do Streamlit)
except Exception as exc:  # nasem_dairy exige NumPy 1.x; pyarrow recente exige NumPy 2
    st.set_page_config(page_title="MuuFeed")
    st.error("Ambiente incompatível: o pyarrow não carregou. O nasem_dairy exige NumPy 1.x. "
             "Recrie o ambiente com Python 3.12 e rode `pip install -r requirements.txt` "
             f"(detalhe: {exc})")
    st.stop()

st.set_page_config(page_title="MuuFeed", page_icon="🐄", layout="wide")
aplicar_tema()
iniciar_estado()

ROTAS = {"Painel": pages.pagina_painel, "Lote": pages.pagina_lote,
         "Ingredientes e preços": pages.pagina_ingredientes, "Formular dieta": pages.pagina_formular,
         "Resultados": pages.pagina_resultados}

with st.sidebar:
    st.markdown("### 🐄 MuuFeed")
    st.radio("Navegação", PAGINAS, key="nav", label_visibility="collapsed")
    st.divider()
    st.caption("Formulador: " + ("conectado" if formulador_conectado() else "não conectado"))
    st.caption("Referência: NASEM 2021 (nasem_dairy). Execução 100% local.")

ROTAS[st.session_state["nav"]]()
