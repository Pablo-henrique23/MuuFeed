# MuuFeed v16 — diagnóstico de sódio e fontes PDF

Patch incremental para instalação **sobre a v15**. Não requer os ZIPs antigos.

## Mudanças

1. Ao ativar **Exigir sódio absorvido** na tela **Formular dieta**, a interface verifica se os ingredientes disponíveis incluem uma fonte **concentrada reconhecida** de sódio. Se não incluir, mostra um aviso **antes** da execução e um botão que leva de volta à sugestão de ingredientes, com a opção de exibir sal habilitada. Nenhum ingrediente é incluído sem confirmação do usuário.
2. Quando o SLSQP não retorna candidata com Na ativo e sem fonte concentrada identificada, a mensagem de inviabilidade aponta o conjunto de ingredientes como possível causa, sem afirmar inviabilidade matemática/nutricional universal. Os déficits aproximados do otimizador permanecem disponíveis.
3. Na tela de resultados, os **aspectos não avaliados** são identificados como **limitações de cobertura** do protótipo, e não como causa automática do fracasso da otimização. Os diagnósticos de falha continuam visíveis.
4. No PDF, a coluna Fonte das regras opcionais de FDN, amido e fNDF passa a ser `NASEM 2021; limite do usuário`. Este termo é mais preciso que “exigência do usuário”, pois contempla **limites mínimos e máximos**.

## Instalação (na raiz do projeto já atualizado para a v15)

```bash
cd ~/MuuFeed
git add . && git commit -m 'checkpoint antes do v16'
unzip -o ~/Downloads/muufeed_v16_diagnostico_sodio_patch.zip
python -m pytest -q
./init.sh
```

## Verificação manual

- No fluxo assistido, selecione alimentos tradicionais e alternativas, **sem sal**. Na tela de formulação, marque `Exigir sódio absorvido`. Deve surgir o aviso e o botão de retorno.
- Pressione o botão de retorno; na sugestão, a caixa de **exibir o sal opcional** deve estar habilitada. O ingrediente **continua desmarcado** e requer confirmação.
- Caso escolha incluir o sal, confirme disponibilidade, preço e **máximo de inclusão definido por profissional** na página Ingredientes e preços. **O MuuFeed não sugere dose de sal.**
- Repita a formulação e confira se o resultado explica a falha, ou se a candidata cumpre a exigência de Na caso encontrada.
- Exporte PDF com FDN mínima e/ou amido máximo e confira `NASEM 2021; limite do usuário` na seção 7.

## Avisos científicos

- Não encontrar candidata pelo SLSQP não demonstra inviabilidade nutricional global.
- Um alimento não identificado como fonte concentrada ainda pode conter sódio. O aviso não substitui o NASEM.
- O modelo implementado permanece limitado a vacas **em lactação**; apoiar outra destinação econômica que envolva categorias animais distintas exige a implementação e validação de outros estados fisiológicos.
- As mensagens de limitação permanecem, e **nenhuma equação NASEM nem composição nutricional foi alterada**.
