"""Curadoria transparente para o fluxo assistido: NÃO é uma recomendação nutricional.

Não procura um conjunto 'ótimo' de alimentos, não presume estoque/preços, e não
insere premixes minerais (cujo balanço não está implementado). A dieta continua
sujeita à verificação parcial pelo motor NASEM.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Sugestao:
    uid: str
    nome_original: str
    nome_pt: str
    grupo: str
    motivo: str
    preco_ilustrativo: float | None
    opcional: bool = False  # alternativas contextuais começam desmarcadas


# Os nomes são entradas existentes no catálogo NASEM e na tabela de preços de DEMONSTRAÇÃO.
# A seleção é uma regra de composição de conjunto candidato, não um limite de inclusão.
CANDIDATOS_LACTACAO = (
    ("Corn silage, typical", "Volumoso", "Opção de volumoso para compor o conjunto inicial."),
    ("Bermudagrass hay", "Volumoso", "Segunda fonte volumosa candidata; confirmar disponibilidade."),
    ("Corn grain dry, medium grind", "Energético", "Fonte concentrada de amido para comparação econômica."),
    ("Citrus pulp, dry", "Energético", "Fonte energética alternativa ao milho no conjunto de candidatos."),
    ("Soybean meal, solvent 48CP", "Proteico", "Ingrediente proteico candidato para o balanço de MP."),
    ("Canola meal", "Proteico", "Alternativa proteica para comparação de custo e composição."),
)


# Curadoria contextual auditável: não é cálculo de exigências nem recomendação
# nutricional. Inclui apenas alternativas para o produtor analisar disponibilidade.
# Os valores que selecionam cada ramo são critérios de organização da interface,
# não limiares científicos ou limites de alimentação.
def _alternativas_do_lote(lote) -> tuple[tuple[str, str, str], ...]:
    leite = float(getattr(lote, "leite_kg_dia", 25.0))
    dias = int(getattr(lote, "dias_lactacao", 120))
    if leite >= 30 or dias <= 90:
        return (
            ("Sorghum grain, dry, ground", "Energético", "Alternativa energética em cenário de maior produção/início de lactação; confirmar viabilidade."),
            ("DDGS, high protein", "Proteico", "Alternativa proteica para comparação; revisar a composição e possíveis limites de uso."),
            ("Soybean hulls", "Fibroso", "Subproduto fibroso para ampliar o conjunto; não substitui fibra fisicamente efetiva."),
        )
    if leite < 20 or dias >= 200:
        return (
            ("Alfalfa meal", "Fibroso", "Alternativa de alimento fibroso para avaliação; classificação não implica fibra efetiva."),
            ("Wheat bran", "Subproduto", "Subproduto disponível no catálogo para comparação de preço e nutrientes."),
            ("Sunflower meal", "Proteico", "Alternativa proteica para comparação; confirmar disponibilidade e preço."),
        )
    return (
        ("Soybean hulls", "Fibroso", "Subproduto fibroso para avaliar alternativas; não substitui volumoso fisicamente efetivo."),
        ("Wheat bran", "Subproduto", "Alternativa para comparação econômica e de composição no perfil informado."),
        ("Cottonseed meal", "Proteico", "Fonte proteica alternativa para comparação; verificar limites apropriados com responsável técnico."),
    )


def sugerir_ingredientes(lote, catalogo, *, incluir_fonte_sodio: bool = False,
                        ampliar_pelo_lote: bool = False) -> tuple[list[Sugestao], list[str]]:
    """Seleciona apenas nomes exatos presentes na biblioteca; sem preços inventados.

    Retorna (sugestões, avisos). Não altera estado, catálogo ou requisição.
    """
    if lote is None:
        return [], ["Cadastre o lote antes de pedir uma sugestão."]
    if lote.estado != "Lactating Cow":
        return [], ["O modo assistido está disponível apenas para vacas em lactação. Use o modo manual para outros estados."]
    if lote.validar()[0]:
        return [], ["O lote contém erros de validação. Corrija-os antes de sugerir ingredientes."]
    por_nome = {str(r.nome_original): r for r in catalogo.tabela.itertuples(index=False)}
    saida, avisos = [], []
    candidatos = CANDIDATOS_LACTACAO
    if ampliar_pelo_lote:
        candidatos += _alternativas_do_lote(lote)
    if incluir_fonte_sodio:
        candidatos += (("Sodium chloride (salt)", "Mineral",
                        "Fonte de sódio e cloro; exige preço real e máximo de inclusão definido por responsável técnico."),)
    for nome, grupo, motivo in candidatos:
        alimento = por_nome.get(nome)
        if alimento is None:
            avisos.append(f"Ingrediente '{nome}' não encontrado na biblioteca instalada; ignorado.")
            continue
        if not 0 < float(alimento.ms_pct) <= 100:
            avisos.append(f"Matéria seca inválida de '{nome}'; ignorado.")
            continue
        preco = catalogo.precos_ilustrativos.get(alimento.uid)
        saida.append(Sugestao(alimento.uid, nome, alimento.nome_pt, grupo, motivo, preco,
                             opcional=nome not in {n for n, _, _ in CANDIDATOS_LACTACAO}))
    if ampliar_pelo_lote:
        avisos.append("Alternativas escolhidas por regras simples sobre leite e dias de lactação; "
                      "isso não comprova adequação nutricional nem preço atual. "
                      "Só a formulação posterior avalia os nutrientes do conjunto confirmado.")
    if not saida:
        avisos.append("Nenhum ingrediente candidato válido encontrado. Utilize o modo manual.")
    return saida, avisos
