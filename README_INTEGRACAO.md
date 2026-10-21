# Integração do núcleo experimental ao MuuFeed

1. Faça um commit/checkpoint antes de alterar o projeto.
2. Copie `formulation_engine.py` para a raiz do projeto.
3. Copie `services/nasem_adapter.py` para a pasta `services`.
4. Copie `install_integration.py` para a raiz e rode `python install_integration.py`.
5. Configure a variável de ambiente:

   ```bash
   export MUUFEED_FORMULADOR=services.nasem_adapter:NasemFormulador
   streamlit run app.py
   ```

6. Informe consumo diário de MS na aba **Formular dieta**. Não há valor padrão: o usuário deve trazer medição ou estimativa fundamentada. Selecione pelo menos **dois ingredientes**, com preços e MS válidos.
7. **Teste preferencial:** use os quatro ingredientes do exemplo NASEM e os valores do experimento anterior, informando o total de MS original. Outro cenário pode não ter solução.
8. Execute `python -m pytest -q`, verifique a página Resultados e o PDF. A integração **não certifica adequação nutricional**; só verifica total de MS, energia e proteína e restrições operacionais.

## Pendências ANTES da demonstração final

- A lógica NASEM usa `nd.demo('lactating_cow_test')` como template de vários parâmetros ainda não fornecidos pelo formulário. Completar a entrada de todos os parâmetros relevantes e documentar hipóteses.
- Cálculos são locais (SLSQP), não garantem ótimo global. Falha em encontrar candidato **não equivale a inviabilidade demonstrada**.
- Adicionar regras verificadas sobre FDN, FDN forragem, amido e minerais e controles de limites de inclusão.
- Corrigir invalidação de resultado quando mudarem ingredientes, preços, limites ou consumo de MS. O script de patch não implementa essa invalidação; bloqueie exportação quando entradas divergirem da requisição calculada.
- Checar relatório financeiro e estados do PDF; apresentar status experimental em destaque.
- Realizar teste ponta a ponta e registrar versões do pacote, Python e biblioteca de alimentos.
