"""Audita TODOS os alimentos reais da biblioteca NASEM instalada.

Uso: python scripts/auditar_catalogo_nutricional.py
Saída: auditoria_catalogo_nasem.csv (uma linha por ingrediente).

Não modifica o CSV original e NÃO substitui valores nutricionais ausentes por zero.
Ausência pontual de nutriente no NASEM pode ser legítima: reportar != inventar.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
from services.forage_ndf import classificar_forragem
from services.feed_science import (
    classificar_uso, referencia_inclusao, proteina_bruta_valida,
    FONTES_NNP, limite_explicito_obrigatorio, FONTE_BIBLIOTECA,
)

NUTRIENTES_MONITORADOS = (
    'Fd_NDF', 'Fd_ADF', 'Fd_Lg', 'Fd_CP', 'Fd_St', 'Fd_WSC',
    'Fd_CFat', 'Fd_Ash', 'Fd_Ca', 'Fd_P', 'Fd_Mg', 'Fd_K',
    'Fd_Na', 'Fd_Cl', 'Fd_S',
)


def auditar(biblioteca: pd.DataFrame) -> pd.DataFrame:
    """Uma linha auditável por UID NASEM, sem alterar os dados de referência."""
    essenciais = {'UID', 'Fd_Name', 'Fd_DM', 'Fd_Type', 'Fd_Category'}
    faltando = sorted(essenciais.difference(biblioteca.columns))
    if faltando:
        raise ValueError(f'CSV NASEM sem colunas estruturais: {faltando}')
    # Auditoria transversal: qualquer coluna de composição NASEM é contabilizada,
    # mesmo que este protótipo não a use como restrição da otimização.
    colunas_nasem = [c for c in biblioteca.columns if c not in
                     ('UID', 'Fd_Name', 'Fd_Type', 'Fd_Category')]
    uid_duplicado = biblioteca['UID'].duplicated(keep=False)
    nome_duplicado = biblioteca['Fd_Name'].duplicated(keep=False)
    linhas = []
    for pos, (_, linha) in enumerate(biblioteca.iterrows()):
        nome = str(linha['Fd_Name'])
        forage, origem = classificar_forragem(
            nome, feed_type=linha['Fd_Type'], feed_category=linha['Fd_Category'])
        dm = pd.to_numeric(linha['Fd_DM'], errors='coerce')
        dm_ok = pd.notna(dm) and math.isfinite(float(dm)) and 0 < float(dm) <= 100
        ausentes, invalidos, presentes = [], [], []
        for col in NUTRIENTES_MONITORADOS:
            if col not in biblioteca.columns:
                ausentes.append(col + ' (coluna não existe)')
                continue
            num = pd.to_numeric(linha[col], errors='coerce')
            if pd.isna(num):
                ausentes.append(col)
            elif not math.isfinite(float(num)) or not (
                proteina_bruta_valida(nome, float(num)) if col == "Fd_CP"
                else 0 <= float(num) <= 100
            ):
                invalidos.append(col)
            else:
                presentes.append(col)
        todos_ausentes = [c for c in colunas_nasem if pd.isna(linha[c])]
        # Segunda passagem pelos 84 campos de referência: valida estrutura
        # numérica (sem inventar o mesmo intervalo para unidades diferentes).
        outros_nao_numericos, outros_nao_finitos = [], []
        for col in colunas_nasem:
            if col in NUTRIENTES_MONITORADOS or col == 'Fd_DM' or pd.isna(linha[col]):
                continue
            try:
                n = float(linha[col])
            except (TypeError, ValueError):
                outros_nao_numericos.append(col)
            else:
                if not math.isfinite(n):
                    outros_nao_finitos.append(col)
        registro_repetido = bool(uid_duplicado.iloc[pos] or nome_duplicado.iloc[pos])
        grupo, nota_uso, fonte_uso = classificar_uso(nome, linha['Fd_Category'])
        referencia_pct, condicoes, fonte_limite = referencia_inclusao(nome)
        linhas.append({
            'UID': linha['UID'], 'nome_nasem': nome,
            'tipo_nasem': linha['Fd_Type'], 'categoria_nasem': linha['Fd_Category'],
            'fdn_forragem_classificacao': ('FORRAGEM' if forage is True else
                                           'NAO_FORRAGEM' if forage is False else 'PENDENTE'),
            'origem_classificacao': origem,
            'ms_valida': bool(dm_ok),
            'uid_ou_nome_duplicado': registro_repetido,
            'total_campos_nasem': len(colunas_nasem),
            'campos_nasem_com_dados': len(colunas_nasem) - len(todos_ausentes),
            'campos_nasem_ausentes': '; '.join(todos_ausentes),
            'fdn_total_disponivel': 'Fd_NDF' in presentes,
            'amido_disponivel': 'Fd_St' in presentes,
            'nutrientes_disponiveis': len(presentes),
            'nutrientes_monitorados': len(NUTRIENTES_MONITORADOS),
            'nutrientes_ausentes': '; '.join(ausentes),
            'nutrientes_invalidos': '; '.join(invalidos),
            'proteina_bruta_equivalente_nnp': nome in FONTES_NNP,
            'uso_lactacao_triagem': grupo,
            'alerta_uso': nota_uso,
            'fonte_alerta': fonte_uso,
            'exige_maximo_explicito': limite_explicito_obrigatorio(nome, linha['Fd_Category']),
            'referencia_inclusao_tmr_pct_ms': referencia_pct,
            'condicoes_da_referencia': condicoes,
            'fonte_inclusao': fonte_limite,
            'fonte_classificacao': FONTE_BIBLIOTECA,
            'campos_adicionais_nao_numericos': '; '.join(outros_nao_numericos),
            'campos_adicionais_nao_finitos': '; '.join(outros_nao_finitos),
            'situacao': ('REVISAO_NECESSARIA' if forage is None or not dm_ok or invalidos or registro_repetido or outros_nao_numericos or outros_nao_finitos
                         else 'OK_COM_LACUNAS' if ausentes else 'OK'),
        })
    return pd.DataFrame(linhas)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='auditoria_catalogo_nasem.csv')
    args = parser.parse_args()
    from services.feed_catalog import carregar_biblioteca_bruta
    biblioteca = carregar_biblioteca_bruta()
    tabela = auditar(biblioteca)
    saida = Path(args.output)
    tabela.to_csv(saida, index=False, encoding='utf-8-sig')
    n = len(tabela)
    classificada = int((tabela['fdn_forragem_classificacao'] != 'PENDENTE').sum())
    ndf_ok = int(tabela['fdn_total_disponivel'].sum())
    st_ok = int(tabela['amido_disponivel'].sum())
    dm_ok = int(tabela['ms_valida'].sum())
    revisao = tabela[tabela['situacao'] == 'REVISAO_NECESSARIA']
    alertas_uso = int((tabela['uso_lactacao_triagem'] != 'NUTRICIONAL_A_VALIDAR').sum())
    campos = int(tabela['total_campos_nasem'].max()) if n else 0
    print(f'Cobertura: {campos} colunas NASEM examinadas por ingrediente; '
          'valores ausentes são apenas reportados.')
    print(f'Ingredientes NASEM: {n} | classificação fNDF: {classificada}/{n} | '
          f'MS válida: {dm_ok}/{n}')
    print(f'FDN total cadastrada: {ndf_ok}/{n} | amido cadastrado: {st_ok}/{n} '
          '(ausência não é zero)')
    print(f'Arquivo de auditoria: {saida.resolve()}')
    print(f'Auditoria sem valores alterados: {len(tabela)} alimentos; '
          f'{alertas_uso} com atenção específica de uso, '
          f'{int(tabela["exige_maximo_explicito"].sum())} exigem teto explícito se selecionados.')
    print('Referências individuais no CSV são guias condicionais para consulta; '
          'NÃO são máximos de segurança impostos automaticamente.')
    if n != 284:
        print(f'AVISO: Esperávamos 284 itens na versão testada; a biblioteca instalada possui {n}.')
    if not revisao.empty:
        print(f'REVISÃO NECESSÁRIA ({len(revisao)}):')
        for linha in revisao.head(30).itertuples(index=False):
            print(f'  {linha.nome_nasem} — {linha.origem_classificacao}; '
                  f'MS válida={linha.ms_valida}; invalidos={linha.nutrientes_invalidos}')
        print('Não declarar catálogo integralmente classificado antes de corrigir as pendências.')
        return 2
    print('OK: todos os itens têm classificação fNDF e MS válida, sem valores nutricionais inválidos.')
    print('ATENÇÃO: OK na auditoria não equivale a alimento liberado para inclusão sem avaliação.')
    print('ATENÇÃO: nutrientes ausentes são registrados, não substituídos nem validados automaticamente.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
