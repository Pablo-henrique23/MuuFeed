# Patch MuuFeed v12 — revisão de formulário, sugestão contextual e documentação

**Aplicar sobre:** versão atual do MuuFeed **após** `muufeed_revisao_pos_testes_patch.zip` (e após o patch de raça condicional).

## Correções
1. Corrige dois testes AST que buscavam o controle `st.button`, embora o formulário atualmente utilize `st.form_submit_button`. Mantém o seletor de raça fora do `st.form`, com aparecimento imediato do nome de outra raça.
2. Acrescenta HELP nos campos de produção média, gordura e proteína do leite. Esses campos são dados medidos/estimados do cenário, não metas alcançadas automaticamente.
3. Mantém seis candidatos fixos e acrescenta, por opção habilitada na interface, **três alternativas contextuais** selecionadas por produção/dias de lactação. As alternativas extras começam **desmarcadas**. Os preços são **ilustrativos** (ou permanecem sem preço se não houver referência); o usuário deve validar preço/disponibilidade. Não há seleção nutricional validada ou recomendação de inclusão.
4. Melhora HELP da FDN de forragens com a referência condicional NASEM 2021 (fNDF 19%, FDN 25%, amido máx. 30% para determinadas hipóteses de ração total e tamanho de partículas).
5. Atualiza README/backlog e documenta limitação observada em versão externa do `nasem_dairy` para `calculate_Ca_Mlk`. O MuuFeed não modifica o pacote externo.

## Instalação
```bash
cd ~/MuuFeed
git add . && git commit -m "checkpoint antes do v12"
unzip -o ~/Downloads/muufeed_v12_form_sugestao_testes_patch.zip
python -m pytest -q
./init.sh
```

## Verificar na UI
- No lote, alternar Holandesa/Jersey/Outra raça: o campo de nome aparece somente para Outra raça.
- Salvar lote e conferir que o botão continua disponível.
- Nos campos de produção/gordura/proteína do leite, observar os HELP.
- Em Sugestão automática, alternar a opção de alternativas contextuais: seis candidatos fixos, mais três opcionais quando marcada; os três adicionais não são selecionados automaticamente.
- Experimentar perfis de lotes com leite ≥30 kg/d ou início de lactação vs. leite <20 kg/d ou lactação mais tardia: alternativas diferentes.
- Confirmar ingredientes e verificar que não há formulação sem preço e disponibilidade.
- Em Formular dieta, abrir avançado FDN de forragens e ler HELP.

## Testes executados aqui
- 150 testes de regressão sem Streamlit, NASEM ou PyArrow: passaram.
- Todos os arquivos Python foram compilados com sucesso.
- A suíte completa e os fluxos Streamlit/NASEM requerem seu ambiente, já configurado.

Não houve alteração nas equações NASEM, SLSQP, função objetivo ou PDF deste patch.
