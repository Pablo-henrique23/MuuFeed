# MuuFeed — patch v15 (22/10/2026)

**Aplicar diretamente sobre a v14 já instalada** (`muufeed_v14_auditoria_cientifica_patch.zip`). Nenhum ZIP intermediário é necessário.

```bash
cd ~/MuuFeed
git add . && git commit -m "checkpoint antes do v15"
unzip -o ~/Downloads/muufeed_v15_auditoria_e_regras_pdf_patch.zip
python -m pytest -q
python scripts/auditar_catalogo_nutricional.py
./init.sh
```

## Por que a auditoria dizia 284 revisões?

`Fd_Libr` é texto de referência bibliográfica em todos os 284 ingredientes da biblioteca, não um nutriente. A v14 tentou convertê-lo em número e produziu **284 falsos positivos**. Agora continua contado na cobertura de 84 campos, mas não como atributo numérico; as 15 grandezas nutricionais monitoradas seguem verificadas. No CSV compartilhado, o único campo `campos_adicionais_nao_numericos` era `Fd_Libr`; não havia outras inconsistências. Portanto os resultados esperados são **216 OK, 68 OK_COM_LACUNAS, 0 REVISÃO_NECESSÁRIA**. Não inventamos nem alteramos valores NASEM.

## PDF: seção 7 legível

As regras listam quantidades efetivas e seus limites, mantendo as unidades e decimais brasileiros. Exemplos:

- `Energia metabolizável: 62,85 >= 52,12 Mcal/dia`
- `Cálcio absorvido: 53,24 >= 53,24 g/dia`
- `FDN: 41,41% MS >= 25,00% MS`
- `Amido: 20,79% MS <= 30,00% MS`

A coluna **Fonte** apresenta `NASEM 2021` nas exigências e `NASEM 2021 + usuário` quando os teores vêm da biblioteca e o limite é fornecido pelo usuário. A seção 8 explica essas origens. O aplicativo ainda usa `nasem_dairy` nos cálculos; apenas o texto do PDF mudou.

O gerador PDF **não recalcula a dieta**: usa indicadores estruturados já disponíveis. Dados ausentes não são inventados e conservam a explicação original. A matemática do NASEM, o SLSQP, os preços e a composição não foram alterados.

## Validação

Na máquina do usuário: suíte completa com dependências NASEM, Streamlit e PyArrow. Nesse ambiente de preparação: 186 testes locais passaram (excluídos 4 conjuntos dependentes do ambiente).
