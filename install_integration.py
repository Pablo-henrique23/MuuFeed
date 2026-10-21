"""Aplica mudanças MINIMAS na interface já existente. Rode uma vez na raiz do repo.

Antes: git commit -am 'checkpoint antes da integracao'
Depois: revise `git diff` e rode os testes. Falha se o repo mudou.
"""
from pathlib import Path


def patch(path, old, new):
    p = Path(path)
    s = p.read_text(encoding='utf-8')
    if new in s:
        print('Já aplicado:', path)
        return
    if old not in s:
        raise RuntimeError(f'Não encontrei trecho esperado em {path}. Integração manual necessária. NÃO sobrescrevi o arquivo.')
    p.write_text(s.replace(old, new, 1), encoding='utf-8')
    print('Atualizado:', path)


patch('models/contracts.py',
      'class OpcoesFormulacao:\n    objetivo: str = "minimizar_custo_vaca_dia"',
      'class OpcoesFormulacao:\n    objetivo: str = "minimizar_custo_vaca_dia"\n    consumo_ms_kg_dia: Optional[float] = None  # Entrada explícita; não é estimativa automática')
patch('models/contracts.py',
      '"otimo", "inviavel"',
      '"otimo", "candidata_experimental", "inviavel"')
patch('ui/pages.py',
      '"demonstracao": "Cenário demonstrativo (não calculado)", "otimo": "Dieta candidata calculada",',
      '"demonstracao": "Cenário demonstrativo (não calculado)", "otimo": "Dieta candidata calculada",\n    "candidata_experimental": "Candidata experimental (avaliação parcial)",')
patch('ui/pages.py',
      'if res and res.status == "otimo" else None',
      'if res and res.status in ("otimo", "candidata_experimental") else None')
patch('ui/pages.py',
      'bool(res and res.status == "otimo")',
      'bool(res and res.status in ("otimo", "candidata_experimental"))')
patch('ui/pages.py',
      '    elif res.status == "otimo":\n        banner("ok", res.mensagem',
      '    elif res.status in ("otimo", "candidata_experimental"):\n        banner("warn" if res.status == "candidata_experimental" else "ok", res.mensagem')
patch('ui/pages.py',
      'res.status in ("otimo", "demonstracao")',
      'res.status in ("otimo", "candidata_experimental", "demonstracao")')
patch('ui/pages.py',
      'if (lote and res.status == "otimo") else None',
      'if (lote and res.status in ("otimo", "candidata_experimental")) else None')
patch('ui/pages.py',
      '    req, erros = montar_requisicao()\n',
      '''    # O consumo de MS é informado, não presumido. Campo da formulação experimental.
    consumo_ms = st.number_input(
        "Consumo estimado de matéria seca (kg MS/vaca/dia)", min_value=0.1,
        value=None, step=0.5, format="%.2f", key="form_consumo_ms",
        help="Obrigatório neste protótipo; deve vir de medição/estimativa técnica do lote, não de valor padrão.")
    req, erros = montar_requisicao()
    if req is not None:
        req.opcoes.consumo_ms_kg_dia = consumo_ms
''')
print('Concluído. Defina MUUFEED_FORMULADOR=services.nasem_adapter:NasemFormulador')
