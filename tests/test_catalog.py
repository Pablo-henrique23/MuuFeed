import json
import pandas as pd
import pytest
from importlib.resources import files
from services.feed_catalog import CatalogoIngredientes, DATA_DIR, normalizar


@pytest.fixture(scope="module")
def cat():
    return CatalogoIngredientes()


def test_carrega_biblioteca_completa(cat):
    bruta = pd.read_csv(files("nasem_dairy.data.feed_library").joinpath("NASEM_feed_library.csv"))
    assert len(cat.tabela) == len(bruta) == 284
    assert cat.tabela["uid"].is_unique


def test_valores_originais_nao_modificados(cat):
    bruta = pd.read_csv(files("nasem_dairy.data.feed_library").joinpath("NASEM_feed_library.csv"))
    assert cat._bruta.equals(bruta)
    assert list(cat.tabela["uid"]) == list(bruta["UID"])
    assert list(cat.tabela["ms_pct"]) == list(bruta["Fd_DM"])


def test_busca_portugues_ingles_e_acentos(cat):
    assert "Farelo de soja, solvente (48 PB)" in set(cat.buscar("farelo soja")["nome_pt"])
    assert "Soybean meal, solvent 48CP" in set(cat.buscar("soybean meal")["nome_original"])
    assert len(cat.buscar("calcario")) > 0 and len(cat.buscar("CALCÁRIO")) == len(cat.buscar("calcario"))
    assert len(cat.buscar("xyzinexistente")) == 0


def test_filtro_por_categoria(cat):
    cats = cat.categorias()
    assert all(cat.buscar("", [cats[0]])["categoria_pt"] == cats[0])


def test_mapeamentos_apontam_para_ingredientes_existentes(cat):
    nomes = set(cat.tabela["nome_original"])
    assert set(json.loads((DATA_DIR / "feed_names_pt.json").read_text(encoding="utf-8"))) <= nomes
    precos = json.loads((DATA_DIR / "demo_prices.json").read_text(encoding="utf-8"))["precos"]
    assert set(precos) <= nomes and all(p > 0 for p in precos.values())
    assert len(cat.precos_ilustrativos) == len(precos)


def test_catalogo_completo_tem_traducao_pt(cat):
    # A auditoria de 22/10 apontava 90 pendentes; agora todos têm rótulo PT.
    assert len(cat.tabela) == 284
    assert cat.tabela["traduzido"].all()
    assert cat.tabela["nome_pt"].str.len().gt(0).all()
    # Identificador original permanece intacto para o motor.
    assert cat.tabela["nome_original"].notna().all()


def test_composicao_marca_ausentes_como_none(cat):
    sem_ca = cat.tabela[cat._bruta["Fd_Ca"].isna().values].iloc[0]["uid"]
    comp = {c["Componente"]: c["Valor"] for c in cat.composicao(sem_ca)}
    assert comp["Cálcio"] is None and comp["Matéria seca (MS)"] is not None


def test_normalizar():
    assert normalizar("  Calcário ") == "calcario"
