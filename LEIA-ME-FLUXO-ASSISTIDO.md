# MuuFeed — fluxo assistido (21/10/2026)

## Instalação

Faça um checkpoint com git e, na raiz do projeto, extraia `muufeed_fluxo_assistido_patch.zip`.

```bash
cd ~/MuuFeed
git add . && git commit -m 'checkpoint: antes do fluxo assistido'
unzip -o ~/Downloads/muufeed_fluxo_assistido_patch.zip
python -m pytest -q
export MUUFEED_FORMULADOR=services.nasem_adapter:NasemFormulador
streamlit run app.py
```

## Como testar

1. Salve um lote **em lactação**.
2. Navegue para **Sugestão automática** (no menu lateral ou botão do Painel).
3. Confira os alimentos propostos, marque apenas os disponíveis e edite seus preços (R$/kg matéria natural).
4. Confirme a disponibilidade e clique em **Usar ingredientes confirmados**.
5. A tela **Ingredientes e preços** se abrirá; revise e adicione/remova ingredientes se desejar.
6. Na tela **Formular dieta**, forneça o consumo estimado de matéria seca. FDN mínima e amido máximo são opcionais.
7. Formule. A dieta é uma **candidata experimental**, sujeita às verificações parciais descritas no relatório.

## Escopo técnico

- **Não altera** `formulation_engine.py`, `services/nasem_adapter.py`, `services/financeiro.py`, nem `services/pdf_report.py`.
- Usa curadoria explícita de 2 volumosos, 2 ingredientes energéticos e 2 proteicos, identificados pelo nome exato na biblioteca NASEM. **Não** seleciona um ingrediente com base na produção de leite, peso ou estoque, e **não** afirma ser nutricionalmente ótimo; a seleção depende da validação do lote (vacas em lactação).
- O agricultor confirma disponibilidade, pode editar os preços (valores iniciais de demonstração), e só então os alimentos são enviados ao otimizador real.
- A seleção assistida **substitui** a seleção anterior apenas quando o usuário confirma essa ação; preços e limites de inclusão de ingredientes comuns são preservados.
- O modo manual continua disponível.
- Os nutrientes ainda não verificados permanecem não avaliados. SLSQP não garante mínimo global. O motor não estima automaticamente ingestão de MS.

## Arquivos alterados
- `services/ingredient_suggestion.py` (novo)
- `tests/test_ingredient_suggestion.py` (novo)
- `ui/pages.py`
- `ui/state.py`
- `app.py`

## Testes
5 testes próprios do seletor + 58 regressões do módulo de contratos, PDF, rótulos e financeiro passaram neste ambiente. A suíte completa exige `streamlit`, `nasem_dairy` e `pyarrow` instalados; execute no seu `.venv`.
