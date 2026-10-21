"""Estado da sessão (`st.session_state`) e montagem da requisição para o formulador."""
from __future__ import annotations

import streamlit as st

from models import Ingrediente, Lote, RequisicaoFormulacao, validar_ingredientes
from services.feed_catalog import CatalogoIngredientes

PAGINAS = ["Painel", "Lote", "Sugestão automática", "Ingredientes e preços", "Formular dieta", "Resultados"]


@st.cache_resource(show_spinner="Carregando a biblioteca de ingredientes NASEM…")
def get_catalogo() -> CatalogoIngredientes:
    return CatalogoIngredientes()


def iniciar_estado() -> None:
    ss = st.session_state
    ss.setdefault("nav", PAGINAS[0])
    ss.setdefault("lote", None)          # Lote validado
    ss.setdefault("selecionados", {})    # uid -> {preco, origem, disponivel, min_mn, max_mn}
    ss.setdefault("resultado", None)     # ResultadoFormulacao
    ss.setdefault("data_ref_precos", None)
    ss.setdefault("requisicao_resultado", None)  # requisição que originou o resultado atual
    if "_ir_para" in ss:                 # navegação programática, antes de criar o widget `nav`
        ss["nav"] = ss.pop("_ir_para")


def ir_para(pagina: str) -> None:
    st.session_state["_ir_para"] = pagina
    st.rerun()


def adicionar(uid: str) -> None:
    cat = get_catalogo()
    preco = cat.precos_ilustrativos.get(uid)
    st.session_state["selecionados"][uid] = {
        "preco": preco, "origem": "ilustrativo" if preco is not None else "",
        "disponivel": True, "min_mn": None, "max_mn": None,
    }


def ingredientes_disponiveis() -> list[Ingrediente]:
    cat, saida = get_catalogo(), []
    for uid, d in st.session_state["selecionados"].items():
        if not d["disponivel"]:
            continue
        r = cat.obter(uid)
        saida.append(Ingrediente(uid, r.nome_original, r.nome_pt, float(r.ms_pct), d["preco"], d["origem"],
                                 True, d["min_mn"], d["max_mn"]))
    return saida


def montar_requisicao() -> tuple[RequisicaoFormulacao | None, list[str]]:
    erros: list[str] = []
    lote = st.session_state.get("lote")
    if lote is None:
        erros.append("Caracterize o lote na página Lote.")
    ings = ingredientes_disponiveis()
    erros += validar_ingredientes(ings)
    if erros:
        return None, erros
    data = st.session_state.get("data_ref_precos")
    return RequisicaoFormulacao(lote, ings, data_ref_precos=data.isoformat() if data else None), []
