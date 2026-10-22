# MuuFeed v10 — roteiro de verificação no ambiente real

## O que mudou

- Campo **Destinação econômica** removido do modelo de dados, cadastro, resultados e PDFs (escopo da aplicação permanece exclusivamente **vacas em lactação para produção de leite**).
- Formulário original v10 oferecia somente **Holandesa** e **Jersey**. O complemento genérico deste patch acrescenta uma opção explícita `An_Breed='Other'`, experimental e com aviso de aproximação, para não confundir com parametrização específica. Entradas desconhecidas sem a escolha explícita continuam rejeitadas.
- Estado fisiológico no formulário é vaca em lactação, único estado efetivamente suportado pelo formulador.
- Nova opção independente, **desmarcada por padrão**, para exigir **Mg, Cl e K absorvidos**, em g/dia, utilizando o NASEM para oferta e exigência. Pode ser ativada com Ca/P e/ou Na.
- Os indicadores minerais continuam no relatório como diagnóstico quando a restrição não estiver ativada.
- Limites superiores, fibra fisicamente efetiva, vitaminas, água e DCAD **não** foram implementados. Uma dieta com todos os seis minerais atendidos **não** é garantia de adequação ou de ausência de excesso.

## Instalação

```bash
cd ~/MuuFeed
git add . && git commit -m 'checkpoint: antes do motor v10'
unzip -o ~/Downloads/muufeed_v10_patch.zip
python -m pytest -q
python scripts/verificar_release_v10.py
./init.sh
```

Se usar `init.sh`, reinicie o processo Streamlit após atualizar. A tela antiga pode conservar widgets/cache da sessão anterior até o reinício.

## Teste rápido de regressão — use dados ilustrativos, NÃO dieta para fornecimento real

1. Cadastre o lote de referência anterior: Holandesa, 30 vacas, 820,8 dias, 624,8 kg, 1ª lactação, 100 dias lactando, leite 25,062 kg/d, gordura 4,55%, proteína 3,66%.
2. Confirme que NÃO existem campos de destinação econômica e que não é possível selecionar Vaca seca. A opção de raça genérica só deve ser usada com a ressalva experimental e após o verificador específico.
3. Use o modo assistido, confirme os ingredientes/preços, CMS manual de 24,521 kg MS/dia e teto operacional de 60% de MS. Para Na, se for disponibilizar sal no cenário experimental, mantenha máximo por ingrediente definido e documentado. Não estabeleça doses automaticamente.
4. **Controle**: deixe Ca/P, Na e Mg/Cl/K desmarcados. Gere PDF e confira que os seis balanços absorvidos são somente diagnósticos.
5. **Teste novo**: ative apenas Mg/Cl/K. O resultado pode mudar, custar mais ou não encontrar candidata. Em caso de candidata, o PDF deve registrar `R_MG_ABS`, `R_CL_ABS` e `R_K_ABS` nas regras e as três restrições atendidas. Em caso de falha, a interface deve apresentar um diagnóstico de tentativa, **nunca uma dieta não validada como se estivesse aprovada**.
6. **Teste combinado**: marque também Ca/P e Na com uma fonte de sódio confirmada e máximo configurado. Novamente, nenhuma solução é resultado aceitável do teste; não force doses para apresentar uma dieta.
7. Confira análise de dieta existente e seu PDF, idade, raça, preços e avisos.

**Sem validação clínica:** compare apenas testes de software; não usar formulações para alimentar animais.
