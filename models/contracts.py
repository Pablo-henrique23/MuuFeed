"""Contratos de dados entre a interface e o formulador.

Sem dependência de Streamlit. O formulador real recebe um `RequisicaoFormulacao`
e devolve um `ResultadoFormulacao`. Unidade-base interna: kg de MATÉRIA SECA (MS)
por vaca/dia; a matéria natural (MN) é derivada pelo teor de MS do alimento.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
import math
from services.breed import para_raca_nasem, utiliza_raca_generica, AVISO_RACA_GENERICA
from typing import Optional

DIAS_POR_ANO = 365.25   # constantes de conversão de unidade, não são parâmetros nutricionais
DIAS_POR_MES = 30.4375
ESTADOS = {"Lactating Cow": "Vaca em lactação", "Dry Cow": "Vaca seca"}

# Hipóteses padrão dos campos avançados. NÃO são medições: a interface as sinaliza ao usuário.
# Origem: exemplo `lactating_cow_test` do pacote nasem_dairy (ver docs/INTERFACE.md).
PADROES_AVANCADOS = {"bcs": 3.0, "lactose_pct": 4.85, "peso_maduro_kg": 700.0, "dias_gestacao": 0}

# Limites de PLAUSIBILIDADE de entrada (evitam erros de digitação). Não são regras nutricionais.
LIMITES = {
    "n_vacas": (1, 100000, "vacas"), "idade_dias": (365, 365.25 * 30, "dias"),
    "peso_kg": (200, 1000, "kg"), "ordem_lactacao": (1, 15, ""),
    "dias_lactacao": (0, 800, "dias"), "leite_kg_dia": (0, 100, "kg/dia"),
    "gordura_pct": (1, 10, "%"), "proteina_pct": (1, 7, "%"), "bcs": (1, 5, ""),
    "lactose_pct": (3, 6, "%"), "peso_maduro_kg": (300, 1100, "kg"), "dias_gestacao": (0, 300, "dias"),
}
ROTULOS = {
    "n_vacas": "Número de vacas", "idade_dias": "Idade", "peso_kg": "Peso médio",
    "ordem_lactacao": "Ordem de lactação", "dias_lactacao": "Dias em lactação",
    "leite_kg_dia": "Produção de leite", "gordura_pct": "Gordura do leite",
    "proteina_pct": "Proteína do leite", "bcs": "Escore de condição corporal",
    "lactose_pct": "Lactose do leite", "peso_maduro_kg": "Peso à maturidade",
    "dias_gestacao": "Dias de gestação",
}


@dataclass
class Lote:
    nome: str = ""
    n_vacas: int = 1
    raca: str = ""
    idade_valor: float = 0.0
    idade_unidade: str = "anos"  # "anos" | "meses" | "dias"
    peso_kg: float = 0.0
    ordem_lactacao: int = 1
    dias_lactacao: int = 0
    estado: str = "Lactating Cow"
    leite_kg_dia: float = 0.0
    gordura_pct: float = 0.0
    proteina_pct: float = 0.0
    bcs: float = PADROES_AVANCADOS["bcs"]
    lactose_pct: float = PADROES_AVANCADOS["lactose_pct"]
    peso_maduro_kg: float = PADROES_AVANCADOS["peso_maduro_kg"]
    dias_gestacao: int = PADROES_AVANCADOS["dias_gestacao"]
    raca_descricao: str = ""  # nome informado; não altera o ramo genérico Other

    @property
    def idade_dias(self) -> float:
        fator = {"anos": DIAS_POR_ANO, "meses": DIAS_POR_MES, "dias": 1.0}.get(self.idade_unidade, 1.0)
        return self.idade_valor * fator

    @property
    def campos_padrao(self) -> list[str]:
        """Campos avançados iguais ao padrão assumido (hipóteses, não medições)."""
        return [k for k, v in PADROES_AVANCADOS.items() if getattr(self, k) == v]

    def validar(self) -> tuple[list[str], list[str]]:
        erros, avisos = [], []
        if not self.nome.strip():
            erros.append("Informe o nome ou a identificação do lote.")
        if self.estado not in ESTADOS:
            erros.append("Estado fisiológico inválido.")
        if self.idade_unidade not in ("anos", "meses", "dias"):
            erros.append("A unidade da idade deve ser anos, meses ou dias.")
        for campo, (lo, hi, un) in LIMITES.items():
            valor = self.idade_dias if campo == "idade_dias" else getattr(self, campo)
            if not (lo <= valor <= hi):
                shown = (f"{lo/DIAS_POR_ANO:.0f} a {hi/DIAS_POR_ANO:.0f} anos"
                         if campo == "idade_dias" else f"{lo} a {hi} {un}".strip())
                erros.append(f"{ROTULOS[campo]} fora do intervalo plausível ({shown}).")
        try:
            if utiliza_raca_generica(self.raca):
                avisos.append(AVISO_RACA_GENERICA)
        except ValueError as exc:
            erros.append(str(exc))
        if self.peso_maduro_kg < self.peso_kg:
            avisos.append("O peso à maturidade é menor que o peso atual; confira os dois valores.")
        if self.campos_padrao:
            nomes = ", ".join(ROTULOS[c].lower() for c in self.campos_padrao)
            avisos.append(f"Hipóteses assumidas por padrão (não medidas): {nomes}.")
        return erros, avisos

    def para_animal_nasem(self) -> dict:
        """Campos do lote nas chaves de `animal_input` do nasem_dairy. O formulador completa o restante.
        `An_Parity_rl` = número de partos (docstring de nasem_dairy.nasem_equations.dry_matter_intake)."""
        return {
            "An_StatePhys": self.estado, "An_Parity_rl": self.ordem_lactacao,
            "An_Breed": para_raca_nasem(self.raca),
            "An_AgeDay": self.idade_dias, "An_BW": self.peso_kg, "An_BW_mature": self.peso_maduro_kg,
            "An_BCS": self.bcs, "An_LactDay": self.dias_lactacao, "An_GestDay": self.dias_gestacao,
            "Trg_MilkProd": self.leite_kg_dia, "Trg_MilkFatp": self.gordura_pct,
            "Trg_MilkTPp": self.proteina_pct, "Trg_MilkLacp": self.lactose_pct,
        }  # a raça é parte do animal_input, não só metadado


@dataclass
class Ingrediente:
    uid: str
    nome_original: str
    nome_pt: str
    ms_pct: float
    preco_mn_brl_kg: Optional[float] = None
    origem_preco: str = ""  # "ilustrativo" | "informado" | ""
    disponivel: bool = True
    min_kg_mn: Optional[float] = None  # limites definidos pelo usuário, kg de MN/vaca/dia
    max_kg_mn: Optional[float] = None

    @property
    def preco_ms_brl_kg(self) -> Optional[float]:
        if self.preco_mn_brl_kg is None or self.ms_pct <= 0:
            return None
        return self.preco_mn_brl_kg / (self.ms_pct / 100)

    def limites_ms(self) -> tuple[Optional[float], Optional[float]]:
        f = self.ms_pct / 100
        return (None if self.min_kg_mn is None else self.min_kg_mn * f,
                None if self.max_kg_mn is None else self.max_kg_mn * f)


def validar_ingredientes(ings: list[Ingrediente]) -> list[str]:
    """Valida unidades, finitude e limites operacionais antes do cálculo."""
    erros: list[str] = []
    if not ings:
        erros.append("Selecione ao menos um ingrediente disponível.")
    for i in ings:
        try:
            preco = float(i.preco_mn_brl_kg)
        except (ValueError, TypeError):
            preco = float("nan")
        if not math.isfinite(preco) or preco <= 0:
            erros.append(f"Informe o preço (R$/kg de MN) de {i.nome_pt}.")
        try:
            ms = float(i.ms_pct)
        except (ValueError, TypeError):
            ms = float("nan")
        if not math.isfinite(ms) or not 0 < ms <= 100:
            erros.append(f"Matéria seca inválida para {i.nome_pt} (0 < MS <= 100%).")
        limites = []
        for nome, valor in (("mínimo", i.min_kg_mn), ("máximo", i.max_kg_mn)):
            if valor is None:
                limites.append(None)
                continue
            try:
                numero = float(valor)
            except (ValueError, TypeError):
                numero = float("nan")
            if not math.isfinite(numero) or numero < 0:
                erros.append(f"Em {i.nome_pt}, {nome} de inclusão deve ser finito e não negativo.")
            limites.append(numero)
        if all(v is not None and math.isfinite(v) for v in limites) and limites[0] > limites[1]:
            erros.append(f"Em {i.nome_pt}, o mínimo é maior que o máximo.")
    return erros


@dataclass
class OpcoesFormulacao:
    objetivo: str = "minimizar_custo_vaca_dia"
    consumo_ms_kg_dia: Optional[float] = None  # Entrada explícita; não é estimativa automática
    min_ndf_pct_dm: Optional[float] = None  # Limite opcional definido pelo usuário, % da MS
    max_starch_pct_dm: Optional[float] = None  # Limite opcional definido pelo usuário, % da MS
    max_ether_extract_pct_dm: Optional[float] = None  # Triagem condicional de extrato etéreo; não é limite universal
    min_forage_ndf_pct_dm: Optional[float] = None  # FDN de forragem opcional, % da MS
    require_absorbed_ca_p: bool = False  # opcional: duas restrições adicionais calculadas pelo NASEM
    require_absorbed_na: bool = False  # opcional: exigência de sódio ABSORVIDO pelo NASEM
    require_absorbed_mg_cl_k: bool = False  # opcional: Mg, Cl e K absorvidos/exigidos NASEM
    consumo_ms_origem: str = "informado"  # "informado" ou "estimado_nrc2001"; documentar hipótese
    max_share_ingredient_pct_dm: Optional[float] = None  # teto operacional do usuário, NÃO limite nutricional


@dataclass
class RequisicaoFormulacao:
    lote: Lote
    ingredientes: list[Ingrediente]
    opcoes: OpcoesFormulacao = field(default_factory=OpcoesFormulacao)
    data_ref_precos: Optional[str] = None  # ISO 8601, quando o usuário informa

    def to_dict(self) -> dict:
        return asdict(self)


STATUS_VALIDOS = {"otimo", "candidata_experimental", "inviavel", "escopo_nao_suportado", "erro", "nao_conectado", "demonstracao"}


@dataclass
class ItemDieta:
    uid: str
    nome: str
    kg_ms: float
    kg_mn: float
    custo_brl: Optional[float] = None  # R$/vaca/dia
    preco_mn_brl_kg: Optional[float] = None  # preço unitário usado pelo formulador (R$/kg MN)


@dataclass
class Indicador:
    chave: str
    rotulo: str
    unidade: str
    ingerido: Optional[float] = None
    exigido: Optional[float] = None
    status: str = "informativo"  # "atende" | "viola" | "nao_avaliado" | "informativo"


@dataclass
class RegraAcionada:
    id: str
    descricao: str
    fonte: str = ""


@dataclass
class Restricao:
    id: str
    descricao: str
    status: str  # "atendida" | "violada" | "nao_avaliada"
    detalhe: str = ""


@dataclass
class ResultadoFormulacao:
    """Não existe campo "dieta completa" de propósito: o contrato só descreve o que foi verificado."""
    status: str
    mensagem: str = ""
    itens: list[ItemDieta] = field(default_factory=list)
    custo_vaca_dia: Optional[float] = None
    indicadores: list[Indicador] = field(default_factory=list)
    regras: list[RegraAcionada] = field(default_factory=list)
    restricoes: list[Restricao] = field(default_factory=list)
    nao_avaliadas: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    modelo_referencia: str = ""
    id_formulacao: str = ""   # preenchido pelo serviço (ou "DEMONSTRACAO")
    executada_em: str = ""    # ISO 8601, preenchido pelo serviço
