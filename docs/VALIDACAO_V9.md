# MuuFeed v9 — Verificações de catálogo, escopo e limites superiores

## Correções incluídas

- `Holandesa` (maiúsculas indiferentes) e `Jersey` continuam convertidas, respectivamente, em `Holstein` e `Jersey` no campo `An_Breed`. Nenhum cálculo nutricional alterado pelo mapeamento.
- As **90 traduções pendentes** do relatório de auditoria foram cadastradas em `data/feed_names_pt.json`; os identificadores NASEM e toda a composição continuam inalterados.
- A busca por português e inglês é preservada, inclusive sem acentos, através de `CatalogoIngredientes.buscar`.
- Para excesso mineral, a aplicação distingue a **exigência mínima de cloro** de uma **concentração máxima tolerável**. Não há máximo tolerável determinado para cloro isolado no capítulo Minerals do NASEM (2021). O livro menciona 3% de NaCl TOTAL na MS como máximo tolerável histórico para vacas lactantes (NRC 2005); **não é recomendação de inclusão**. O código produz avisos de triagem, não um atestado de dieta segura.

## Instalação sobre v8 com patch de tradução já aplicado

```bash
cd ~/MuuFeed
git add . && git commit -m 'checkpoint antes da revisao v9'
unzip -o ~/Downloads/muufeed_v9_patch.zip
python -m pytest -q
python scripts/verificar_release_v9.py
./init.sh
```

## Conferência manual rápida

2. Tentar **Produção de carne**: deve mostrar que não é suportada, em vez de inventar fórmula.
3. Buscar `soro de leite fresco` e `Whey fresh`: resultados com o mesmo UID e nome NASEM.
4. Buscar `selenito de sódio` e `Selenite sodium`; conferir o mesmo resultado.
6. Testar um cenário com sal: o relatório deve dizer que 3% de NaCl é **máximo tolerável histórico**, não prescrição, e que cloro > 200% da exigência mínima não comprova toxicidade.

## Validação neste ambiente da assistência

- `136 passed` na suíte que não exige Streamlit, PyArrow ou `nasem_dairy` real.
- 11 testes dependentes do `nasem_dairy` e 1 de `pyarrow` não foram executáveis aqui; suíte com Streamlit igualmente depende do ambiente do usuário.
- Preview do PDF de formulação e da análise renderizados e inspecionados.

## Pendências científicas (não implementar automaticamente antes do prazo)

- Limites superiores de minerais por espécie/classe, interação com água e DCAD; não confundir exigência mínima com toxicidade.
- Fontes dietéticas e qualidade da matéria-prima reais, limites específicos de inclusão, fibra fisicamente efetiva e vitaminas.
- Formulador de carne e dupla aptidão: exigiriam modelo e validação diferentes do atual NASEM leiteiro.
