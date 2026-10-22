# MuuFeed v8 — Verificação de raça e sódio

**Escopo:** etapa incremental do sistema especialista experimental. Não é prescrição de dieta nem validação para alimentação animal.

## Raça

- A interface permite Holandesa e Jersey e não aceita silenciosamente outras raças para formulação.
- `Lote.para_animal_nasem()` usa `services/breed.py`: Holandesa → `An_Breed=Holstein`; Jersey → `An_Breed=Jersey`.
- A formulação e o analisador passam o mesmo valor ao `animal_input` do `nasem_dairy`.
- `python scripts/verificar_raca_nasem.py` verifica a execução real do NASEM para ambas as raças no cenário de referência. O script não prova validação científica completa.

## Sódio

- Ao selecionar **Exigir sódio ABSORVIDO**, o motor compara `Abs_NaIn` com `An_Na_req` do mesmo resultado NASEM (g/dia).
- Se a restrição não é satisfeita, nenhuma dieta pode ser aceita como candidata factível para o cenário. **Isso não prova impossibilidade de alimentar o lote**, apenas que nenhuma candidata foi encontrada no conjunto fornecido.
- O novo fluxo assistido oferece opção de considerar **Sodium chloride (salt)**, nome exato da biblioteca. Ela vem **desmarcada por padrão**.
- O sal só pode entrar se o usuário confirmar disponibilidade e preço e informar o limite máximo em **kg de matéria natural/vaca/dia** na tela Ingredientes e preços. **Nenhuma dose é calculada ou recomendada pelo aplicativo.** Não use qualquer quantidade sugerida por testes para alimentar animais sem zootecnista/veterinário.
- Os preços do catálogo são ilustrativos. O usuário deve substituí-los por custo real.
- A restrição de Na é um **mínimo de oferta absorvida**, sem verificação de excesso, limites superiores ou balanço cátion-aniônico completo. Cálcio, fósforo, magnésio, cloro, potássio e demais nutrientes não são automaticamente validados.

## Instalação e testes

```bash
cd ~/MuuFeed
git add . && git commit -m "checkpoint antes do v8"
unzip -o ~/Downloads/muufeed_v8_patch.zip
python -m pytest -q
python scripts/verificar_raca_nasem.py
./init.sh
```

**Demonstração controlada:**
1. Cadastre o mesmo lote Holandesa usado nos testes anteriores.
2. Confirme que a formulação sem Na ativado se comporta como antes.
3. Em Sugestão automática, marque a opção de considerar sal, confirme e edite o preço.
4. Em Ingredientes e preços, informe um máximo operacional para esse ingrediente somente como cenário de teste, com valor definido por responsável técnico; nunca use dose automática.
5. Em Formular, mantenha o mesmo CMS, demais limites e preços. Marque **Exigir sódio absorvido** e execute.
6. Confira ingestão e exigência absorvidas de Na, lista de regras, preço, e observe se aparece uma candidata ou diagnóstico de nenhuma solução encontrada.
7. Mesmo com Na atendido, o PDF deve continuar com o aviso de candidata experimental e indicar outras restrições pendentes.

Se o `pytest` passar, mas o NASEM real falhar, encaminhe o erro antes de usar o modo mineral na apresentação. **Não remova a etiqueta experimental.**
