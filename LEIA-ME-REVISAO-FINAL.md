# Revisão pós-testes A–G (sobre versão com campo de raça condicional)

Instale ESTE patch sobre a versão que já inclui `muufeed_fix_nome_outra_raca_condicional.zip`.

Mudanças: HELP para ECC, lactose, peso à maturidade e gestação; identificação clara da
lista fixa do modo assistido e origem ilustrativa dos preços; FDN de forragens passa para
um expander avançado; excluída a frase redundante do fim do PDF de formulação.

**Não** altera o motor de otimização, as exigências minerais, o cálculo financeiro,
a seleção de raça ou os contratos de dados. Os avisos de dieta experimental seguem.
**Não habilita vacas secas** (fluxo nutricional específico ainda sem validação).

Instale na raiz do projeto e execute:

```bash
unzip -o ~/Downloads/muufeed_revisao_pos_testes_patch.zip
python -m pytest -q
./init.sh
```

Verifique visualmente os quatro ícones `?` dos campos avançados, a explicação no
modo assistido, o expander de FDN de forragens e o novo PDF sem a frase redundante.
