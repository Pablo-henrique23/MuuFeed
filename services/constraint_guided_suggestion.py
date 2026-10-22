"""Pré-triagem DINÂMICA dos candidatos do NASEM por composição e limites.

Não calcula exigências NASEM de energia, proteína metabolizável ou minerais.
Não prescreve inclusões: seleção preliminar sujeita a confirmação do usuário.
Utiliza LP químico (FDN, amido, fNDF e teto) para identificar candidatos que
*podem* sustentar os limites; a viabilidade final cabe ao motor NASEM/SLSQP.
Preços da demonstração são ilustrativos, não cotações.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import pandas as pd
from scipy.optimize import linprog

from services.feed_science import eh_so_bezerro, limite_explicito_obrigatorio
from services.forage_ndf import classificar_forragem
from services.ingredient_suggestion import Sugestao


@dataclass(frozen=True)
class LimitesTriagem:
    min_ndf_pct_dm: float | None = None
    max_starch_pct_dm: float | None = None
    min_forage_ndf_pct_dm: float | None = None
    max_share_ingredient_pct_dm: float | None = None
    require_ca_p: bool = False
    require_na: bool = False
    require_mg_cl_k: bool = False
    max_ether_extract_pct_dm: float | None = None


@dataclass(frozen=True)
class ResultadoTriagem:
    sugestoes: tuple[Sugestao, ...]
    avisos: tuple[str, ...]
    composicao_possivel: bool
    candidatos_examinados: int
    selecionados_preliminarmente: int
    origem: str = "Programação linear preliminar com composição NASEM e preços disponíveis"


def _numero(valor, minimo=0, maximo=100):
    try:
        v = float(valor)
    except (ValueError, TypeError):
        return None
    return v if math.isfinite(v) and minimo <= v <= maximo else None


def _grupo(categoria: str, eh_forragem: bool, cp: float, fdn: float):
    if eh_forragem:
        return "Volumoso"
    if categoria == "plant protein" or cp >= 25:
        return "Proteico"
    if fdn >= 32:
        return "Fibroso"
    return "Energético"


def _candidatos(lote, catalogo, selecionados):
    """Somente ingredientes com preço conhecido (real ou ilustrativo) e composição suficiente.

    Uso restringido por natureza (aditivos, premixes, NNP, rações de bezerro) NÃO
    entra automaticamente; esses ingredientes exigem decisão individual.
    """
    b = getattr(catalogo, "_bruta", None)
    if b is None or not {"Fd_Name", "Fd_NDF", "Fd_St", "Fd_CP", "Fd_DM"}.issubset(b.columns):
        return []
    indexed = {str(l.nome_original): l for l in catalogo.tabela.itertuples(index=False)}
    saida = []
    for item in b.itertuples(index=False):
        nome = str(item.Fd_Name)
        reg = indexed.get(nome)
        if reg is None or eh_so_bezerro(nome) or limite_explicito_obrigatorio(nome, getattr(item, "Fd_Category", "")):
            continue
        tipo = getattr(item, "Fd_Type", "")
        categoria = getattr(item, "Fd_Category", "")
        forage, _ = classificar_forragem(nome, feed_type=tipo, feed_category=categoria)
        if forage is None:
            continue
        ms = _numero(getattr(item, "Fd_DM", None), 0.0001, 100)
        nd = _numero(getattr(item, "Fd_NDF", None))
        starch = _numero(getattr(item, "Fd_St", None))
        cp = _numero(getattr(item, "Fd_CP", None))
        fat = _numero(getattr(item, "Fd_CFat", None))
        if any(x is None for x in (ms, nd, starch, cp)):
            continue
        anterior = selecionados.get(str(reg.uid), {})
        preco = anterior.get("preco") if anterior.get("preco") is not None else catalogo.precos_ilustrativos.get(reg.uid)
        if preco is None or _numero(preco, 0.0001, 1000000) is None:
            continue
        saida.append({"nome": nome, "uid": str(reg.uid), "pt": reg.nome_pt,
                      "grupo": _grupo(str(categoria).casefold(), bool(forage), cp, nd),
                      "forage": bool(forage), "ndf": nd/100, "starch": starch/100,
                      "fndf": nd/100 if forage else 0., "cp": cp/100,
                      "ee": (fat/100 if fat is not None else None),
                      "preco_ms": float(preco)/(ms/100), "preco": float(preco)})
    return saida


def sugerir_por_restricoes(lote, catalogo, limites: LimitesTriagem, *,
                           selecionados: dict | None = None) -> ResultadoTriagem:
    if lote is None:
        return ResultadoTriagem((), ("Cadastre o lote antes de sugerir.",), False, 0, 0)
    if lote.estado != "Lactating Cow":
        return ResultadoTriagem((), ("A pré-triagem suporta apenas vacas em lactação.",), False, 0, 0)
    erros, _ = lote.validar()
    if erros:
        return ResultadoTriagem((), ("Corrija os dados do lote antes de sugerir ingredientes.",), False, 0, 0)
    avisos = []
    for value, rotulo in ((limites.min_ndf_pct_dm, "FDN mínima"),
                          (limites.max_starch_pct_dm, "Amido máximo"),
                          (limites.min_forage_ndf_pct_dm, "FDN de forragens mínima"),
                          (limites.max_share_ingredient_pct_dm, "Teto por ingrediente"),
                          (limites.max_ether_extract_pct_dm, "Extrato etéreo máximo")):
        if value is not None and _numero(value) is None:
            return ResultadoTriagem((), (f"Valor inválido: {rotulo}.",), False, 0, 0)
    pool = _candidatos(lote, catalogo, selecionados or {})
    if limites.max_ether_extract_pct_dm is not None:
        pool = [item for item in pool if item["ee"] is not None]
    if not pool:
        return ResultadoTriagem((), ("Não há dados suficientes de composição e preço para a pré-triagem. Use seleção manual.",), False, 0, 0)
    cap = limites.max_share_ingredient_pct_dm
    if cap is not None and float(cap) <= 0:
        return ResultadoTriagem((), ("O teto deve ser maior que zero.",), False, len(pool), 0)
    if cap is not None and len(pool)*float(cap) < 100-1e-8:
        avisos.append("Teto matematicamente incompatível até com o conjunto total de ingredientes com preço conhecido; reveja limites ou confirme outros alimentos.")
        return ResultadoTriagem((), tuple(avisos), False, len(pool), 0)
    A, B = [], []
    if limites.min_ndf_pct_dm is not None:
        A.append([-p["ndf"] for p in pool]); B.append(-float(limites.min_ndf_pct_dm)/100)
    if limites.max_starch_pct_dm is not None:
        A.append([p["starch"] for p in pool]); B.append(float(limites.max_starch_pct_dm)/100)
    if limites.min_forage_ndf_pct_dm is not None:
        A.append([-p["fndf"] for p in pool]); B.append(-float(limites.min_forage_ndf_pct_dm)/100)
    if limites.max_ether_extract_pct_dm is not None:
        A.append([p["ee"] for p in pool]); B.append(float(limites.max_ether_extract_pct_dm)/100)
    bound = float(cap)/100 if cap is not None else 1.
    result = linprog([p["preco_ms"] for p in pool], A_ub=A or None, b_ub=B or None,
                     A_eq=[[1.0]*len(pool)], b_eq=[1.], bounds=[(0.,bound)]*len(pool),
                     method="highs")
    if not result.success:
        avisos.append("Pré-triagem de FDN/amido/FDN de forragens e teto: não foi possível compor 100% da MS com os alimentos de preço conhecido. Isso não prova inviabilidade no catálogo completo nem avalia ME/MP/minerais. Revise limites, disponibilidade ou inclua alimentos manualmente.")
        return ResultadoTriagem((), tuple(avisos), False, len(pool), 0)
    # As frações LP identificam candidatos para estudo, NÃO uma dieta formulada.
    ativos = [i for i, x in enumerate(result.x) if x > 1e-7]
    primarios = list(ativos)
    leite = float(getattr(lote, "leite_kg_dia", 25))
    dias = float(getattr(lote, "dias_lactacao", 100))
    grupos = ["Volumoso", "Proteico", "Energético", "Fibroso"]
    def score(p):
        # Priorização auditável por custo, perfil químico e produção do lote;
        # pesos heurísticos de ranqueamento, não requisitos nutricionais.
        quantidade_leite = max(0, leite - 20)/30
        bonus_proteina = (0.9*quantidade_leite * p["cp"]) if p["grupo"] == "Proteico" else 0
        bonus_amido = (0.15*quantidade_leite * p["starch"]) if p["grupo"] == "Energético" else 0
        bonus_fibra = (0.20*p["ndf"]) if p["grupo"] == "Volumoso" and dias >= 200 else 0
        return (p["preco_ms"] - bonus_proteina - bonus_amido - bonus_fibra, p["nome"])
    # Mostrar alternativas de naturezas distintas e manter um pool suficiente
    # para respeitar um teto por ingrediente após confirmação de disponibilidade.
    # Variedade do CONJUNTO CANDIDATO muda segundo lactação e produção.
    # Cotas abaixo são meras cotas para mostrar opções; NÃO são participação
    # da dieta, dose mínima ou prioridade clínica.
    if leite >= 30 or dias <= 90:
        desejados = {"Volumoso": 2, "Proteico": 3, "Energético": 3, "Fibroso": 1}
    elif leite < 20 or dias >= 200:
        desejados = {"Volumoso": 3, "Proteico": 1, "Energético": 1, "Fibroso": 3}
    else:
        desejados = {"Volumoso": 2, "Proteico": 2, "Energético": 2, "Fibroso": 2}
    if limites.min_forage_ndf_pct_dm is not None:
        desejados["Volumoso"] = max(desejados["Volumoso"], 3)
    for grupo in grupos:
        atuais = sum(pool[i]["grupo"] == grupo for i in primarios)
        for i in sorted((i for i,p in enumerate(pool) if p["grupo"] == grupo and i not in primarios),
                        key=lambda i: score(pool[i])):
            if atuais >= desejados[grupo]:
                break
            primarios.append(i); atuais += 1
    min_necessarios = math.ceil(100/float(cap)) if cap else 4
    primarios = list(dict.fromkeys(primarios))
    for i in sorted(range(len(pool)), key=lambda k: score(pool[k])):
        if len(primarios) >= max(min_necessarios, 8):
            break
        if i not in primarios:
            primarios.append(i)
    # Manter os ativos LP assinalados inicialmente, mais complementos suficientes
    # para evitar uma tela com 1 único ingrediente mesmo sem teto.
    obrigatorios = set(ativos)
    for grupo in grupos:
        candidatos_grupo = [i for i in primarios if pool[i]["grupo"] == grupo]
        if candidatos_grupo:
            obrigatorios.add(min(candidatos_grupo, key=lambda i: score(pool[i])))
    for i in primarios:
        if len(obrigatorios) >= max(4, min_necessarios):
            break
        obrigatorios.add(i)
    ordered = sorted(primarios, key=lambda i: (i not in obrigatorios, grupos.index(pool[i]["grupo"]), score(pool[i])))
    sugestoes = []
    for i in ordered:
        p = pool[i]
        lp_used = i in ativos
        motivo = ("Selecionado na pré-triagem matemática dos limites de composição; CONFIRMAR disponibilidade e revisar inclusão."
                  if lp_used else
                  "Alternativa complementar por perfil do lote, composição da biblioteca e custo ilustrativo; não é indicação de uso nutricional.")
        sugestoes.append(Sugestao(p["uid"], p["nome"], p["pt"], p["grupo"], motivo,
                                 p["preco"], opcional=i not in obrigatorios))
    avisos.append(f"Pré-triagem química encontrou uma combinação de referência entre {len(pool)} alimentos com dados e preço conhecidos. São exibidas {len(sugestoes)} opções (inclusive reservas). **Não há validação antecipada de energia, proteína metabolizável, sódio ou demais minerais**: isso ocorrerá na formulação NASEM após sua confirmação.")
    if limites.require_na:
        avisos.append("Você exigiu sódio: o conjunto de alimentos comuns não garante atendimento. Avalie uma fonte de sódio disponível e seu teto com responsável técnico; a inclusão do sal nunca é automática.")
    if limites.require_ca_p or limites.require_mg_cl_k:
        avisos.append("Exigências de minerais absorvidos serão verificadas pelo NASEM na etapa final. A pré-triagem não promete que o conjunto satisfaça esses balanços.")
    return ResultadoTriagem(tuple(sugestoes), tuple(avisos), True, len(pool), len(obrigatorios))


def conferir_selecao_quimica(catalogo, limites: LimitesTriagem, selecionados_uids,
                             *, precos: dict | None = None) -> tuple[bool, str]:
    """Triagem dos ingredientes que o usuário marcou (sem ME/MP/minerais).

    Retorna False para conjunto que não consegue satisfazer limites químicos
    ou para ingrediente fora do conjunto de composição/precificação auditável.
    """
    pool = _candidatos(None, catalogo, precos or {})
    if limites.max_ether_extract_pct_dm is not None:
        pool = [item for item in pool if item["ee"] is not None]
    ids = set(selecionados_uids)
    subset = [p for p in pool if p["uid"] in ids]
    if len(subset) < len(ids):
        return False, "Há ingredientes marcados sem composição/preço elegível à triagem; confira os dados antes de formular."
    if len(subset) < 2:
        return False, "Selecione pelo menos dois ingredientes com composição e preço conhecidos."
    teto = limites.max_share_ingredient_pct_dm
    cap = (float(teto)/100 if teto is not None else 1.)
    if cap <= 0 or len(subset)*cap < 1-1e-8:
        return False, "Os ingredientes marcados não conseguem somar 100% da MS com o teto informado; inclua mais alimentos ou reveja o teto."
    A, B = [], []
    for valor, chave, sinal in ((limites.min_ndf_pct_dm,"ndf",-1),
                               (limites.max_starch_pct_dm,"starch",1),
                               (limites.min_forage_ndf_pct_dm,"fndf",-1),
                               (limites.max_ether_extract_pct_dm,"ee",1)):
        if valor is None:
            continue
        A.append([sinal*p[chave] for p in subset])
        B.append(sinal*float(valor)/100)
    r = linprog([p["preco_ms"] for p in subset], A_ub=A or None, b_ub=B or None,
                A_eq=[[1.]*len(subset)], b_eq=[1.], bounds=[(0.,cap)]*len(subset), method="highs")
    return (True, "A seleção passa pela pré-triagem química. Ainda precisa da verificação NASEM para energia, proteína metabolizável e minerais.") if r.success else (
        False, "Os alimentos marcados não atendem simultaneamente FDN/amido/FDNf e teto na pré-triagem; marque mais alternativas ou ajuste limites com orientação técnica.")
