# Seleção guiada por lote e restrições — MuuFeed v18 (22/10/2026)

## O que foi alterado

Na página **Sugestão automática**, os parâmetros **teto global de participação, FDN mínima, amido máximo, FDN de forragens mínima e grupos minerais** são informados **antes** de escolher os ingredientes. O modo guiado é padrão; o modo assistido anterior permanece como alternativa de compatibilidade.

### Etapa 1 — Priorização e pré-triagem química

1. Lê o catálogo NASEM instalado **sem alterar os valores**; usa apenas ingredientes com composição (MS, FDN, amido e PB) conhecida, classificação fNDF disponível e preço informado ou demonstrativo. Alimentos sem preço não são "completados" artificialmente.
2. Não escolhe automaticamente rações para bezerros, NNP, suplementos minerais/vitamínicos, aditivos e gorduras concentradas que exijam teto individual e avaliação profissional.
3. Monta uma programação **linear** com \(\sum_j x_j=1\), \(0\le x_j\le\mathrm{teto}\), FDN e FDN de forragens mínimas e amido máximo, se o usuário os informou; minimiza o custo *apenas nessa pré-triagem*. A solução serve para identificar **candidatos**, não é uma dieta NASEM final.
4. Apresenta ingredientes ativos nessa pré-triagem e alternativas complementares de origens variadas. As cotas de apresentação mudam conforme produção de leite e dias de lactação, **sem representar metas nutricionais, limites de inclusão ou doses**.
5. Recalcula a viabilidade química **com os ingredientes realmente marcados** após alterações no editor e avisa se a escolha não passa pela pré-triagem. A pessoa deve confirmar disponibilidade e preço antes de continuar.
6. As restrições marcadas são transferidas sem mudança para **Formular dieta**.

### Etapa 2 — Modelo real

O `nasem_dairy` e o otimizador SLSQP continuam verificando **energia metabolizável, proteína metabolizável, Ca/P/Na/Mg/Cl/K absorvidos selecionados**, além dos limites de composição. O modo guiado **não declara antecipadamente** essa viabilidade: o conjunto pode passar pela etapa 1 e falhar na etapa 2.

**Sódio:** fonte como NaCl é mostrada separadamente e **desmarcada**; exige confirmação e teto técnico em `Ingredientes e preços`. Não definir automaticamente doses minerais ou aumentar o máximo para forçar solução.

### Limites e dados de literatura

Alguns ingredientes têm referências *orientativas e condicionais* publicadas (Penn State); se o teto uniforme excede um desses valores, a interface alerta, mas **não define** automaticamente um máximo seguro específico por alimento. Limites superiores, água, vitaminas, DCAD, fibra fisicamente efetiva e interação mineral ainda não estão validados para uso de campo.

Esta seleção exige ingredientes que possuam preço conhecido **na instalação**, não pesquisa preços de mercado. Na demonstração, valores são ilustrativos. **O algoritmo não examina os 284 simultaneamente se parte não tem preço ou composição conhecida**; essas limitações são mostradas.

## Cenário para demonstrar ao júri

1. Lote Holandesa: 675 kg, 25 kg leite/dia, 3,55% gordura, 3,66% proteína e 100 dias em lactação.
2. Acessar **Sugestão automática**. Escolher **teto 30%**, **FDN ≥25%**, **amido ≤30%** e **FDNf ≥19%**.
3. Marcar Ca/P e Na para a etapa final (só serão verificados no NASEM). Selecionar a opção para considerar sal; ele fica desmarcado até ser confirmado; exige teto profissional.
4. Observar a pré-triagem dos ingredientes, retirar alguns e conferir se a mensagem muda quando os limites se tornam matematicamente impossíveis.
5. Confirmar a disponibilidade e os preços. Ir a **Ingredientes e preços**; se incluir sal, informar o teto individual tecnicamente fundamentado.
6. Ir a **Formular dieta** e verificar que **todos os limites já estão preenchidos**, podendo ajustá-los.
7. Formular. Se não houver candidata NASEM, usar o diagnóstico, revisar ingredientes e **não apresentar resultado incompleto como válido**.

## O que é ciência publicada e o que é implementação heurística

- A estrutura de **formulação de menor custo sujeita a desigualdades nutricionais**, e o uso de LP/SQP, é tradicional e tem pesquisa experimental: [J. Dairy Science (2022), DOI 10.3168/jds.2021-20817](https://doi.org/10.3168/jds.2021-20817).
- O NASEM 2021 fornece composição e exigências; combinações de referência de fibra/amido dependem da situação: [NASEM 2021](https://www.ncbi.nlm.nih.gov/books/NBK600603/).
- Referências condicionais de inclusão de subprodutos: [Penn State Extension](https://extension.psu.edu/concentrates-for-dairy-cattle) e [University of Georgia Extension](https://fieldreport.caes.uga.edu/publications/B862/considerations-for-using-by-product-feeds/).
- A **escolha de quantos candidatos exibir por grupo conforme produção e dias de lactação** é heurística do MuuFeed para experiência de uso. **Não é equação nem regra do NASEM.**
- **Vitaminas A, D e E:** os teores dependem de fontes suplementares e armazenamento; não há validação de balanço completo e de inclusão com os dados atuais. [NASEM 2021, capítulo 8](https://www.ncbi.nlm.nih.gov/books/NBK600608/).
