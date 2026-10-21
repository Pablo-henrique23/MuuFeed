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


def sugerir_ingredientes(lote, catalogo) -> tuple[list[Sugestao], list[str]]:
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
    for nome, grupo, motivo in CANDIDATOS_LACTACAO:
        alimento = por_nome.get(nome)
        if alimento is None:
            avisos.append(f"Ingrediente '{nome}' não encontrado na biblioteca instalada; ignorado.")
            continue
        if not 0 < float(alimento.ms_pct) <= 100:
            avisos.append(f"Matéria seca inválida de '{nome}'; ignorado.")
            continue
        preco = catalogo.precos_ilustrativos.get(alimento.uid)
        saida.append(Sugestao(alimento.uid, nome, alimento.nome_pt, grupo, motivo, preco))
    if not saida:
        avisos.append("Nenhum ingrediente candidato válido encontrado. Utilize o modo manual.")
    return saida, avisos
