# Revisão científica do catálogo MuuFeed v14

**Escopo:** auditoria informática da biblioteca NASEM 2021 **instalada** no ambiente do usuário, com 284 ingredientes. A fonte original não é editada. Este documento NÃO certifica segurança de doses nem qualidade de alimentos reais.

## Resultados reais (CSV auditado enviado pelo usuário)

| Item | Antes | Após a correção metodológica |
|---|---:|---:|
| Classificação de FDN de forragem | 283/284 | **284/284** (77 forragens, 207 não forragens) |
| Matéria seca válida | 284/284 | 284/284 |
| FDN total disponível | 281/284 | 281/284 |
| Amido disponível | 281/284 | 281/284 |
| OK em 15 nutrientes monitorados | 212 | **216** |
| OK com alguma lacuna | 67 | **68** |
| REVISAO_NECESSARIA | 5 | **0** para as cinco causas identificadas |

**Importante:** `OK` significa ausência de alerta de integridade e preenchimento nos **15 campos monitorados**. Não significa dieta segura, nem todos os **84 campos** completos. A auditoria verifica todos os 84 campos quanto a preenchimento e tipo numérico (quando presentes), mas não possui intervalo científico independente para todas as variáveis.

### Cinco casos revisados

- **Alfalfa meal:** NASEM classifica o **tipo** como `Forage`, mas a **categoria** como `Plant Protein`. Para fins de FDN química de forragens, a classificação por tipo prevalece **somente nesse caso curado**. Processamento fino pode reduzir o estímulo físico; **a classificação não estima peNDF**.
- **Ammonium chloride, Ammonium phosphate (dibasic), Ammonium sulfate, Urea:** a coluna `Fd_CP` é o **equivalente de proteína bruta**, obtido de N×6,25. Valores superiores a 100% em fontes de nitrogênio não proteico **não são teores físicos de proteína verdadeira**. A correção está restrita a esses NNP explicitamente reconhecidos; qualquer outro alimento com Fd_CP >100% continua sendo sinalizado.
- **Ammonium sulfate, Vit D premix, Vit E premix:** a biblioteca não fornece FDN/amido. Permanecem ausentes; **não se pressupõe 0** sem especificação de pureza/veículo.

### Uso em vacas em lactação

- Seis rações da própria biblioteca dizem `(Fed to calves only)`: o formulador de **vacas em lactação** passa a recusá-las, explicando o motivo. Elas continuam pesquisáveis no catálogo informativo.
- Fontes **NNP**, sais/premixes de **vitaminas e minerais**, **aditivos** e suplementos concentrados de **gordura** exigem **máximo operacional informado pelo usuário** antes da formulação. Exigir um teto **não verifica que ele seja seguro**.
- Referências de inclusão de Penn State são expostas apenas para consulta humana em **seis exemplos**. Não são copiadas para `max_kg_mn`, não são limites universais de toxicidade e não são impostas automaticamente. A UGA usa outras faixas para certos ingredientes, reforçando a dependência de contexto.
- Nenhum alimento ganhou nutrientes ausentes, limite de segurança arbitrário ou preço novo. A biblioteca NASEM original permanece intacta.

## Referências utilizadas

1. National Academies of Sciences, Engineering, and Medicine (NASEM). **Nutrient Requirements of Dairy Cattle**, 8th revised edition, 2021; cap. 19 (*Nutrient Composition of Feeds*), cap. 7 (*Minerals*) e cap. 9 (*Water*). https://www.ncbi.nlm.nih.gov/books/NBK600603/ ; https://www.ncbi.nlm.nih.gov/books/NBK600601/ ; https://www.ncbi.nlm.nih.gov/books/NBK600589/
2. NASEM dairy feed library, metadados originais `Fd_Type`, `Fd_Category`, `Fd_CP`, `Fd_NDF`, `Fd_St`. https://www.cnmnasemdairy.com/library
3. Penn State Extension. **Concentrates for Dairy Cattle**, tabela *Suggested maximum intakes for lactating dairy cattle on various concentrate ingredients*. https://extension.psu.edu/concentrates-for-dairy-cattle
4. John K. Bernard, University of Georgia Cooperative Extension, Bulletin 862. **Considerations for Using By-Product Feeds**, especialmente *Limits on Amounts Fed*, *Nutrient Analysis and Variation*, *Whole Oilseeds*. https://fieldreport.caes.uga.edu/publications/B862/considerations-for-using-by-product-feeds/
5. NASEM (2021), cap. 7 e cap. 9: excesso de enxofre, sulfatos na água e interações minerais exigem exame da **dieta + água**. https://www.ncbi.nlm.nih.gov/books/NBK600600/ ; https://www.ncbi.nlm.nih.gov/books/NBK600589/

## O que ainda não é possível prometer

Não há base para afirmar que 284×84 valores estejam totalmente medidos, nem para definir um limite máximo **seguro e universal** por ingrediente. Mesmo quando a composição média NASEM está disponível, os alimentos reais variam com cultivar, época, armazenamento, processamento e composição de premixes. Para uso real, seria necessário laudo bromatológico e avaliação profissional de todas as restrições nutricionais/operacionais relevantes.

**Comandos após patch:** `python -m pytest -q` e `python scripts/auditar_catalogo_nutricional.py`. A auditoria gera `auditoria_catalogo_nasem.csv`, sem alterar a biblioteca de alimentos.
