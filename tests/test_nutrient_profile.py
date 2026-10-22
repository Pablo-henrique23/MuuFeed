"""Perfil ampliado: cálculos informativos sem atribuir exigências fictícias."""
from dataclasses import replace
import pandas as pd
import pytest

from services.nutrient_profile import calcular_perfil, PERFIL_PERCENTUAL
from services.pdf_report import AVISO_PROFISSIONAL, gerar_relatorio_pdf
from tests.factories import resultado_teste, ingredientes_teste
from tests.test_contracts import lote_ok
from pypdf import PdfReader
import io


def test_percentual_ponderado_e_massa_diaria():
    catalogo = pd.DataFrame([
        {"Fd_Name": "A", "Fd_CP": 10, "Fd_Mg": 0.2},
        {"Fd_Name": "B", "Fd_CP": 30, "Fd_Mg": 0.6},
    ])
    perfil = calcular_perfil(catalogo, {"A": 3, "B": 1})
    assert perfil["proteina_bruta"]["pct_dm"] == pytest.approx(15)
    assert perfil["proteina_bruta"]["g_day"] == pytest.approx(600)
    assert perfil["magnesio"]["pct_dm"] == pytest.approx(.3)
    assert perfil["magnesio"]["g_day"] == pytest.approx(12)
    assert perfil["fda"]["pct_dm"] is None


def test_ausencia_de_composicao_nao_vira_zero():
    catalogo = pd.DataFrame([{"Fd_Name":"A","Fd_CP":15}, {"Fd_Name":"B","Fd_CP":None}])
    res = calcular_perfil(catalogo, {"A":2, "B":1})
    assert res["proteina_bruta"]["pct_dm"] is None
    assert calcular_perfil(catalogo, {"A":2, "B":0})["proteina_bruta"]["pct_dm"] == 15


def test_rejeita_ingrediente_faltante_e_dados_invalidos():
    lib = pd.DataFrame([{"Fd_Name":"A", "Fd_CP":130}])
    assert calcular_perfil(lib,{"A":1})["proteina_bruta"]["pct_dm"] == 130
    with pytest.raises(ValueError, match="ausente"):
        calcular_perfil(lib, {"B": 1})


def test_nao_inclui_micronutrientes_com_unidade_nao_confirmada():
    assert "Fd_Cu" not in (v[1] for v in PERFIL_PERCENTUAL.values())
    assert "Fd_VitA" not in (v[1] for v in PERFIL_PERCENTUAL.values())


def test_pdf_mostra_aviso_profissional_e_limite_fdn_forragens():
    from models import Indicador
    res = replace(resultado_teste("candidata_experimental"), indicadores=[
        Indicador("fdn_forragens","FDN proveniente de forragens", "% da MS", 21., None, "informativo"),
        Indicador("perfil_proteina_bruta","Proteína bruta equivalente", "% da MS", 16., None, "informativo")
    ])
    pdf = gerar_relatorio_pdf(res, lote_ok(), ingredientes_teste())
    texto = " ".join(" ".join(p.extract_text().split()) for p in PdfReader(io.BytesIO(pdf)).pages)
    assert AVISO_PROFISSIONAL in texto
    assert "FDN proveniente de forragens" in texto
    assert "Não configurado" in texto
    assert "Proteína bruta equivalente" in texto
    assert "não há exigência validada" in texto


def test_formulador_propaga_perfil_sem_criar_falsas_regras(monkeypatch):
    import formulation_engine as eng
    from formulation_engine import FeedChoice, FormulationRequest, formulate_diet
    df = pd.DataFrame([
        {"Fd_Name":"A", "Fd_NDF":40,"Fd_St":15,"Fd_Ca":.3,"Fd_P":.2,"Fd_CP":12,"Fd_Mg":.3},
        {"Fd_Name":"B", "Fd_NDF":20,"Fd_St":60,"Fd_Ca":.1,"Fd_P":.3,"Fd_CP":30,"Fd_Mg":.1},
    ])
    monkeypatch.setattr(eng, "load_library", lambda: df)
    class Output:
        def get_value(self, key):
            return {"An_MEIn":60,"Trg_MEuse":50,"An_MPIn_g":2200,"An_MPuse_g_Trg":1900}[key]
    req = FormulationRequest(
        feeds=(FeedChoice("A", 1, 60), FeedChoice("B", 2, 90)),
        animal={"An_StatePhys":"Lactating Cow", "An_AgeDay":821, "An_BW":624,
                "An_LactDay":100,"An_Parity_rl":1},
        equations={"DMIn_eqn":0}, total_dm_kg=12, herd_size=30,
        restarts=2,
    )
    result = formulate_diet(req, evaluate=lambda *args: Output())
    assert result["status"] == "candidata_experimental"
    add = result["nutrient_composition"]["additional_nutrients"]
    assert 12 <= add["proteina_bruta"]["pct_dm"] <= 30
    assert "minerais" in result["constraints_not_checked"]
    assert "proteina_bruta" not in result["constraints_checked"]


def test_analise_dieta_produz_perfil_sem_otimizar(monkeypatch):
    from services import diet_analysis
    from models import Ingrediente, Lote
    feed = pd.DataFrame([{
        "Fd_Name":"Corn silage, typical", "Fd_DM":35, "Fd_NDF":40,
        "Fd_St":30,"Fd_Ca":0.3,"Fd_P":0.25,"Fd_CP":8,"Fd_Mg":0.15}])
    monkeypatch.setattr(diet_analysis, "load_library", lambda: feed)
    class Output:
        def get_value(self,key):
            return dict(An_MEIn=20, Trg_MEuse=30, An_MPIn_g=1000, An_MPuse_g_Trg=1500)[key]
    lote = Lote(nome="Teste", n_vacas=10, raca="Holandesa", idade_valor=821,
                idade_unidade="dias", peso_kg=600, ordem_lactacao=1,
                dias_lactacao=100, leite_kg_dia=25, gordura_pct=4.5, proteina_pct=3.6)
    ing = [Ingrediente("a", "Corn silage, typical", "Silagem", 35, .30)]
    res = diet_analysis.analisar_dieta(lote, ing, {"a":20.}, scenario=(None, {}, {}, None),
                                      evaluate=lambda *args: Output())
    assert res["additional_nutrients"]["proteina_bruta"]["pct_dm"] == 8
    assert res["additional_nutrients"]["magnesio"]["pct_dm"] == .15
    assert res["validated_complete"] is False
