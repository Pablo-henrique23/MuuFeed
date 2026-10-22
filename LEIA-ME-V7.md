# MuuFeed v7 — CMS opcional, teto operacional e resultados mais claros

## Como aplicar sobre o projeto atual (v6)

1. Registre um checkpoint com `git add . && git commit -m "checkpoint: antes do patch v7"`.
2. Extraia `muufeed_v7_patch.zip` **na raiz** de `~/MuuFeed`, sobrescrevendo os arquivos indicados.
3. Rode `python -m pytest -q`. Na máquina de desenvolvimento também execute `python scripts/verificar_nasem_minerais.py`.
4. Reinicie a interface usando `./init.sh`.

## Como testar sem mudar as premissas do teste anterior

Cadastre o lote A1 (624,8 kg, 25,062 kg de leite/dia, 4,55% de gordura, 100 dias em lactação). Na página **Formular dieta**:

- Para **reproduzir os relatórios A1/A2**, selecione **Informar consumo medido ou estimado externamente** e preencha `24.521` kg MS/vaca/dia. Deixe o novo teto opcional vazio. Preserve ingredientes, preços e estado de Ca/P. As dietas devem continuar comparáveis.
- Para testar a nova função, selecione **Estimar a partir do lote (NRC 2001)**. O valor estimado deve ser cerca de **21,48 kg MS/vaca/dia**. Isso muda a quantidade alvo; portanto **não** compare custos/dietas com A1/A2 como se fosse o mesmo experimento.
- Para testar o novo **controle operacional**, mantenha o consumo informado em 24,521, marque Ca/P conforme desejar e configure **Máxima participação por ingrediente = 60% MS** (valor meramente experimental). Confira no resultado que **cada ingrediente** representa no máximo 60% da MS, se houver candidata. Isso pode causar ausência de candidata; nesse caso não há bug: confira diagnóstico.
- Gere PDF e confira avisos nutricionais, especialmente se sódio, cálcio ou cloro ainda estiverem abaixo das exigências.

## O que o patch faz e o que NÃO faz

- O CMS continua sendo uma entrada fixa para o NASEM (`DMIn_eqn=0`). A fórmula NRC 2001 é uma **estimativa opcional externa**, não um cálculo NASEM 2021 nem medição.
- O limite de participação é **operacional e global**, não uma regra universal de nutrição; não valida segurança ou saúde animal.
- Os indicadores informativos estão abreviados; suas informações não foram descartadas: a tela contém o detalhamento e o PDF tem seção de composição.
- O objetivo matemático permanece mínimo custo local, sujeito às restrições efetivamente ativadas.
- Dietas permanecem **experimentais**. Revisão de zootecnista ou veterinário é necessária antes de qualquer uso alimentar.

Fonte para equação do CMS: https://pmc.ncbi.nlm.nih.gov/articles/PMC7825592/

**Correção relevante dos PDFs A1/A2:** com Ca/P ativado, o v6 exibia somente Ca e P, omitindo Mg/Na/Cl/K. O v7 reavalia a dieta final e mostra os seis balanços absorvidos quando presentes. O usuário precisa refazer A2 para verificar o sódio; não suponha que ele atende apenas porque Ca/P atendem.
