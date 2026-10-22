"""Regressões sintéticas sem instalar NASEM/Streamlit."""
from dataclasses import dataclass
from types import SimpleNamespace
from pathlib import Path

import pandas as pd
import pytest

from services.constraint_guided_suggestion import (
    LimitesTriagem, conferir_selecao_quimica, sugerir_por_restricoes)


@dataclass
class LoteStub:
    estado: str = "Lactating Cow"
    leite_kg_dia: float = 25.0
    dias_lactacao: int = 100
    def validar(self):
        return [], []


def _cat():
    base = [
        ("Feno A", "Forage", "Grass/Legume Forage", 91, 67, 7, 12, 1.0),
        ("Feno B", "Forage", "Grass/Legume Forage", 90, 63, 9, 14, 1.2),
        ("Silagem A", "Forage", "Grain Crop Forage", 35, 42, 32, 8, 0.3),
        ("Farelo P", "Concentrate", "Plant Protein", 89, 16, 11, 46, 2.0),
        ("Farelo Q", "Concentrate", "Plant Protein", 90, 20, 10, 41, 1.8),
        ("Grão E", "Concentrate", "Energy Source", 87, 14, 63, 8, 1.1),
        ("Casca S", "Concentrate", "By-Product/Other", 90, 64, 3, 15, 1.3),
        ("Polpa C", "Concentrate", "By-Product/Other", 90, 31, 12, 9, 1.2),
    ]
    bruta, tabela, precos = [], [], {}
    for i,(name,t,cat,dm,nd,st,cp,price) in enumerate(base):
        uid=str(i)
        bruta.append(dict(UID=uid,Fd_Name=name,Fd_Type=t,Fd_Category=cat,Fd_DM=dm,
                          Fd_NDF=nd,Fd_St=st,Fd_CP=cp))
        tabela.append(dict(uid=uid,nome_original=name,nome_pt=name,ms_pct=dm))
        precos[uid]=price
    return SimpleNamespace(_bruta=pd.DataFrame(bruta),tabela=pd.DataFrame(tabela),precos_ilustrativos=precos)


def test_tria_com_teto30_fndf_e_densidade():
    cat=_cat()
    r=sugerir_por_restricoes(LoteStub(),cat,LimitesTriagem(
        min_ndf_pct_dm=25,max_starch_pct_dm=30,min_forage_ndf_pct_dm=19,
        max_share_ingredient_pct_dm=30))
    assert r.composicao_possivel
    assert r.candidatos_examinados==8
    assert len(r.sugestoes)>=4
    ativos=[s.uid for s in r.sugestoes if not s.opcional]
    assert len(ativos)>=4
    ok,txt=conferir_selecao_quimica(cat, LimitesTriagem(25,30,19,30), ativos)
    assert ok,txt


def test_tria_recusa_fndf_impossivel():
    cat=_cat()
    r=sugerir_por_restricoes(LoteStub(),cat,LimitesTriagem(min_forage_ndf_pct_dm=99))
    assert not r.composicao_possivel
    assert not r.sugestoes


def test_tria_detecta_teto_na_selecao_usuario():
    cat=_cat()
    ok,txt=conferir_selecao_quimica(cat,LimitesTriagem(max_share_ingredient_pct_dm=30),["0","1","2"])
    assert not ok and "100%" in txt


def test_opcoes_minerais_nao_prometem_balanco_na_tria():
    r=sugerir_por_restricoes(LoteStub(),_cat(),LimitesTriagem(require_na=True,require_ca_p=True))
    assert r.composicao_possivel
    assert any("NASEM" in a and "não" in a.lower() for a in r.avisos)
    assert all(s.nome_original != "Sodium chloride (salt)" for s in r.sugestoes)


def test_nao_altera_dados_catalogo():
    cat=_cat()
    b=cat._bruta.copy(deep=True)
    sugerir_por_restricoes(LoteStub(),cat,LimitesTriagem())
    pd.testing.assert_frame_equal(b,cat._bruta)


def test_nao_inclui_aditivos_ou_cria_precos():
    cat=_cat()
    novo={"UID":"8", "Fd_Name":"Urea", "Fd_Type":"Concentrate", "Fd_Category":"Plant Protein",
          "Fd_DM":100,"Fd_NDF":0,"Fd_St":0,"Fd_CP":280}
    cat._bruta=pd.concat((cat._bruta,pd.DataFrame([novo])),ignore_index=True)
    cat.tabela=pd.concat((cat.tabela,pd.DataFrame([{"uid":"8","nome_original":"Urea","nome_pt":"Ureia","ms_pct":100}])),ignore_index=True)
    cat.precos_ilustrativos["8"]=0.2
    r=sugerir_por_restricoes(LoteStub(),cat,LimitesTriagem())
    assert r.candidatos_examinados==8
    assert all(s.nome_original!="Urea" for s in r.sugestoes)


def test_ui_limites_antes_da_sugestao_e_transferidos_para_formular():
    s=(Path(__file__).parents[1]/"ui/pages.py").read_text(encoding="utf-8")
    bloco=s.split("def pagina_sugestao_automatica()",1)[1].split("def pagina_ingredientes()",1)[0]
    assert bloco.index('st.subheader("1. Restrições antes da sugestão")') < bloco.index("sugerir_por_restricoes(")
    assert 'ss["assistido_restricoes_para_formular"] = dict(pre)' in bloco
    for key in ("form_share_max", "form_fdn_min", "form_amido_max", "form_fdn_forragem_min",
                "form_minerais_abs", "form_sodio_abs", "form_mg_cl_k_abs"):
        assert f'("{key}",' in s
    assert 'ss.pop("assistido_restricoes_para_formular", None)' in s
    assert "if modo_guiado and not passou_quimica:" in bloco


def test_lista_realmente_varia_com_lote_quando_existem_opcoes():
    cat=_cat()
    extras=[]
    nomes=[("Feno C", "Forage", "Grass/Legume Forage", 90, 64, 10, 13,1.3),
           ("Proteico Z", "Concentrate", "Plant Protein", 90, 15, 9, 39, 2.2),
           ("Proteico Y", "Concentrate", "Plant Protein", 90, 18, 12, 37, 2.4),
           ("Energia Z", "Concentrate", "Energy Source", 88, 12, 65, 11, 1.3),
           ("Energia Y", "Concentrate", "Energy Source", 88, 13, 62, 10, 1.5),
           ("Fibra Z", "Concentrate", "By-Product/Other", 90, 52, 7, 16, 1.4),
           ("Fibra Y", "Concentrate", "By-Product/Other", 90, 51, 6, 16, 1.4)]
    for idx, (name,t,catg,dm,nd,st,cp,price) in enumerate(nomes,8):
        uid=str(idx)
        extras.append(dict(UID=uid,Fd_Name=name,Fd_Type=t,Fd_Category=catg,
                           Fd_DM=dm,Fd_NDF=nd,Fd_St=st,Fd_CP=cp))
        cat.tabela.loc[len(cat.tabela)]=dict(uid=uid,nome_original=name,nome_pt=name,ms_pct=dm)
        cat.precos_ilustrativos[uid]=price
    cat._bruta=pd.concat([cat._bruta,pd.DataFrame(extras)],ignore_index=True)
    low=sugerir_por_restricoes(LoteStub(leite_kg_dia=15,dias_lactacao=230),cat,LimitesTriagem())
    high=sugerir_por_restricoes(LoteStub(leite_kg_dia=38,dias_lactacao=45),cat,LimitesTriagem())
    assert low.composicao_possivel and high.composicao_possivel
    a={s.nome_original for s in low.sugestoes};b={s.nome_original for s in high.sugestoes}
    assert a == b  # Todos os ingredientes elegíveis estão visíveis.
    assert len(a) == low.candidatos_examinados == high.candidatos_examinados
    destaques_low = {s.uid for s in low.sugestoes if "Ingrediente adicional elegível" not in s.motivo}
    destaques_high = {s.uid for s in high.sugestoes if "Ingrediente adicional elegível" not in s.motivo}
    assert destaques_low != destaques_high
