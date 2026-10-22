# Ciência nutricional, fontes e limitações

## NASEM 2021

A execução científica usa o pacote Python `nasem_dairy` com os parâmetros do lote informados pelo usuário e parâmetros complementares ainda herdados do exemplo oficial. A biblioteca de ingredientes não foi alterada. As unidades internas do otimizador são **kg de matéria seca por vaca/dia**; a quantidade comercial e o custo são convertidos por `Fd_DM`.

**Energia metabolizável (ME)** e **proteína metabolizável (MP)** são exigidas pelo otimizador, usando ingestão e exigência retornadas pelo NASEM. **FDN total, FDN de forragens e amido** possuem restrições opcionais definidas pelo usuário; não são recomendações automáticas.

## Minerais: separação imprescindível

O catálogo fornece **composição mineral bruta** (`Fd_Ca`, `Fd_P`, etc.). O teor mineral bruto **não pode ser comparado diretamente** à exigência mineral absorvida.

A versão atual pode ler, do MESMO resultado do NASEM, os pares absorvido versus exigência absorvida:

- Cálcio: `Abs_CaIn` vs `An_Ca_req`, em g/dia.
- Fósforo: `Abs_PIn` vs `An_P_req`, em g/dia.
- Diagnóstico adicional quando disponível: Mg, Na, Cl e K, todos na base absorvida.

A opção **“Exigir cálcio e fósforo ABSORVIDOS”** acrescenta os dois primeiros pares como restrições reais da busca SLSQP. É **desligada inicialmente** para preservar a comparabilidade dos cenários antigos; quando ativada, pode resultar em nenhuma candidata com os ingredientes disponíveis. Se desligada, o balanço é diagnóstico: pode mostrar violação apesar de a candidata atender à ME/MP.

A análise de dieta existente utiliza os mesmos balanços sem alterar quantidades.

## O que ainda NÃO está validado

Fibra fisicamente efetiva; recomendação contextual de limites de FDN/amido; oferta de aminoácidos essenciais em relação às exigências; todas as vitaminas e microminerais; limites máximos seguros por alimento; previsão de ingestão espontânea de MS; ingredientes reais sem análises bromatológicas; possíveis variações entre vacas; modelagem clínica e validação independente. O SLSQP é local e não garante o menor custo global.

**É um sistema de apoio à decisão experimental**, não uma dieta pronta para alimentação real. Uma revisão por médico-veterinário ou zootecnista e dados bromatológicos reais são indispensáveis.

## Fontes consultadas

- NASEM Dairy Python, código do motor: <https://nasem-model-python.readthedocs.io/en/latest/_modules/nasem_dairy/model/nasem.html>
- NASEM Dairy Python, guia de uso: <https://nasem-model-python.readthedocs.io/en/latest/getting_started/index.html>
- NASEM, *Nutrient Requirements of Dairy Cattle*, 8th rev. edition (2021): <https://nap.nationalacademies.org/catalog/25806/nutrient-requirements-of-dairy-cattle-eighth-revised-edition>
- Universidade de Guelph, repositório da implementação: <https://github.com/CNM-University-of-Guelph/NASEM-Model-Python>

### CMS e limite operacional — atualização v7

O CMS não precisa ser informado manualmente na interface: a equação de previsão do NRC 2001 foi implementada como alternativa aproximada, baseada em leite corrigido a 4% de gordura (LCG4%), peso metabólico e semanas de lactação:

`CMS = [0.372 * LCG4% + 0.0968 * BW**0.75] * [1 - exp(-0.192 * (DIM/7 + 3.67))]`

`LCG4% = 0.4 * leite_kg_dia + 15 * gordura_kg_dia`.

Fonte: https://pmc.ncbi.nlm.nih.gov/articles/PMC7825592/

A alimentação final altera o CMS observado e a equação tem erro individual: trata-se de uma **hipótese de cálculo**, não diagnóstico. No NASEM, `Trg_Dt_DMIn` continua fixado ao valor informado ou estimado e `DMIn_eqn=0`.

O teto de participação é apenas **restrição operacional configurada pelo usuário**, aplicada a todos os ingredientes. Não é uma exigência NASEM; valores precisam ser definidos conforme o caso e não servem para validar segurança/adequação nutricional. A minimização de custo permanece local e sujeita aos limites efetivamente configurados. Os minerais absorvidos são reportados ainda que não sejam restrições ativas.
