# MuuFeed v13 — Classificação e auditoria de TODO o catálogo NASEM

## Por que houve o erro

As opções contextuais da v12 incluíram `Soybean hulls`, `Wheat bran` e
`Cottonseed meal`, mas o código da fNDF usava apenas uma pequena lista de
identificadores classificados manualmente. A presença de alimentos não listados
impedia de impor a fNDF mínima, mesmo sendo concentrados/subprodutos.

## Correção

1. A classificação de fNDF usa **Fd_Type/Fd_Category originais da biblioteca NASEM**,
   sendo uma regra genérica para todos os alimentos da instalação (não uma lista
   estática de seis ou quinze alimentos). Se houver conflito, faltarem metadados
   ou o nome for desconhecido, a classificação continua pendente; não se atribui
   `False` silenciosamente.
2. Os nomes já explicitamente curados são fallback para cenários de teste/versões
   da biblioteca sem tipo e categoria.
3. `Soybean hulls`, `Wheat bran`, `Cottonseed meal` e outros concentrados **não
   entram no numerador da FDN de forragens**, ainda que contenham muita FDN.
4. FDN de forragens é distinta da **FDN total** e da **fibra fisicamente efetiva**.
   A falta de NDF de um concentrado não impede calcular fNDF, mas impede impor
   FDN total quando esse valor for necessário.
5. A análise de dieta existente aplica exatamente o mesmo princípio.

## Auditoria de todos os ingredientes

Na raiz do projeto, com `.venv` ativo:

```bash
python scripts/auditar_catalogo_nutricional.py
python -m pytest -q
```

O primeiro comando escreve `auditoria_catalogo_nasem.csv`, **uma linha para cada
UID da biblioteca instalada**, contendo sua classificação de forragem e origem,
validade de MS, disponibilidade de FDN/amido, 15 componentes principais e
**todas as colunas adicionais do CSV NASEM** com dados faltantes discriminados.

- `OK`: classificação, MS e os 15 campos monitorados preenchidos e válidos.
- `OK_COM_LACUNAS`: classificação e MS válidas, porém nutrientes ausentes;
  **não se inventa zero**. Ausências podem ser intencionais na biblioteca.
- `REVISAO_NECESSARIA`: erro de classificação, conflito de metadados, MS
  inválida, nutriente principal fora de 0–100% ou UID/nome repetido.
- Retorno **2** do comando indica revisão necessária. Cole a saída e envie o
  CSV para localizar precisamente os itens antes da apresentação.

**Limites de escopo:** o MuuFeed usa a composição de referência do catálogo
NASEM; não pode certificar experimentalmente todas as características reais de
284 alimentos, sua inocuidade ou níveis máximos de inclusão específicos. O
modelo não altera dados ausentes para simular completude. Uma auditoria
informática não equivale a análise bromatológica de alimentos reais.

## Cenário de regressão recomendado

Selecione as alternativas contextuais (`Soybean hulls`, `Wheat bran`,
`Cottonseed meal`) com silagem de milho e ative fNDF mínima. A mensagem
`Classificação de forragem pendente` **não deve mais aparecer para esses três
alimentos**. Se FDN total/amido forem ativados e faltarem teores NASEM de algum
ingrediente, o sistema deve avisar especificamente que não há dados suficientes.

Se também exigir os seis minerais sem fontes de sódio disponíveis, a ausência
justificada de candidata ainda é possível — isso não é defeito da fNDF.
