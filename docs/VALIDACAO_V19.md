# MuuFeed v19 — Triagem de extrato etéreo e PDF final

## Funcionalidades implementadas nesta versão

- A seleção assistida pode aplicar **limite opcional de extrato etéreo (EE, Fd_CFat, % da MS)** ainda na pré-triagem linear de ingredientes com preço conhecido. Sem dado de EE, o alimento não é elegível à triagem **quando o limite está ativo**.
- O mesmo limite chega à tela Formular dieta e ao motor SLSQP como restrição efetiva. A candidata só é aceita depois de verificar `EE ponderado pela MS <= teto`. A verificação independe do código de saída do otimizador.
- Tela Formular dieta: campo de EE com **valor inicial de 7%**, editável ou desativável (valor vazio). Esse valor é uma **triagem condicional**, não limite máximo seguro universal ou prescrição. Quando o usuário desativa o limite, EE passa a ser informativo, e valores acima de 7% geram aviso descritivo.
- A análise de dieta existente preserva quantidades e emite alerta quando a composição de referência excede o patamar orientativo de 7%.
- PDF de formulação: faixa vermelha repetida, quadro vermelho e notas técnicas redundantes removidos; seção de limites/indicadores e regra de EE permanecem; aviso profissional aparece sem repetição excessiva.
- Aviso da raça `Other` apresentado de forma compreensível; o modelo ainda recebe `An_Breed="Other"`.

## Por que 7%?

A Penn State Extension descreve dietas de vacas leiteiras de maior produção em que a gordura total pode chegar a 6–7% da MS, dependendo do tipo de gordura suplementar. A referência não autoriza usar 7% como limite universal, e **extrato etéreo não equivale à quantidade e ao perfil de ácidos graxos livres no rúmen**.

Fonte: [Penn State Extension — From Feed to Milk: Understanding Rumen Function](https://extension.psu.edu/from-feed-to-milk-understanding-rumen-function).

## Ainda NÃO validado como dieta completa

Os seguintes pontos permanecem fora de uma validação nutricional completa:

- Vitaminas A/D/E: exigência não basta; seriam necessários teores confiáveis dos suplementos, armazenamento e biodisponibilidade. A biblioteca é heterogênea.
- Microminerais e excessos individuais, incluindo interações entre minerais, água, DCAD e saúde do rebanho.
- Fibra fisicamente efetiva: tamanho de partícula real e processamento dos alimentos não são conhecidos a partir da FDN química.
- Limites superiores específicos de cada ingrediente (NNP, gossipol, enxofre, micotoxinas etc.). As referências bibliográficas de inclusão são condicionais.
- Perfil de ácidos graxos e impacto ruminal, apenas parcialmente relacionado a EE.
- Cálculo para outras fases (vacas secas / novilhas / bovinos de corte), fora do escopo validado.
- Equações e parâmetros do NASEM que não são explicitamente fornecidos no formulário; o sistema preserva valores do cenário de demonstração do pacote como hipóteses até revisão individual.
- Comportamento em animais reais: não houve medição bromatológica, avaliação zootécnica nem validação de campo.

**O sistema continua rotulando os resultados como candidatas experimentais e não usa a expressão “dieta nutricionalmente adequada” para afirmar completude.** Isso evita um veredito falso e deixa claras as verificações realmente feitas.

## Sobre os parâmetros complementares do exemplo oficial

`NasemFormulador.formular()` chama `nd.demo("lactating_cow_test")` para obter `animal_input`, `equation_selection` e `infusion_input` completos. Depois substitui **13 campos** com o lote: estado fisiológico, paridade, raça, idade, peso, peso à maturidade, ECC, dias em lactação, dias de gestação, produção e composição do leite. Também fixa a MS declarada/estimada em `Trg_Dt_DMIn` e usa `DMIn_eqn=0`.

Os demais campos, como características ambientais e hipóteses internas do cenário de demonstração, **não provêm do produtor**. A afirmação foi retirada do PDF por preferência de apresentação, mas esse uso permanece documentado e NÃO foi corrigido cientificamente nesta versão. A versão instalada do NASEM pode ser inspecionada com `python scripts/verificar_hipoteses_nasem_v19.py`.

Referência da API: [NASEM Dairy — Getting Started](https://nasem-model-python.readthedocs.io/en/latest/getting_started/index.html).

## Testes necessários antes da entrega

1. `python -m pytest -q` no `.venv` com todas as dependências.
2. `python scripts/verificar_hipoteses_nasem_v19.py` para confirmar a origem dos campos NASEM.
3. Sugestão assistida: teto global 30%, FDN 25%, amido máximo 30%, FDNf 19%, EE máximo 7% e minerais opcionais; confirmar alimentos e avaliar resultado.
4. Testar **EE máximo vazio**: não deve impedir formulação, mas indicador continua informativo e deve alertar quando EE supera 7%.
5. Testar limite EE impossível (por exemplo, abaixo do menor valor presente): a candidata deve ser rejeitada com diagnóstico, nunca rotulada de adequada.
6. Regerar PDF com raça genérica e verificar visualmente a ausência de faixa vermelha, quadro vermelho e notas técnicas solicitadas; o aviso da raça deve aparecer só uma vez.
7. Analisar dieta existente com EE >7%: aviso sobre composição, mantendo quantidades originais.

Nenhuma dessas verificações autoriza uso de dieta real sem profissional.
