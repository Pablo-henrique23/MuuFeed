# MuuFeed — Correção dos nomes de ingredientes (interface PT-BR)

Esta atualização altera **somente rótulos de apresentação**. O catálogo NASEM continua íntegro: `UID`, `Fd_Name`, os parâmetros nutricionais e os dados enviados ao motor não sofrem alterações.

## Aplicação

Na raiz do MuuFeed, faça um checkpoint e extraia o ZIP:

```bash
git add . && git commit -m 'checkpoint antes de traduzir catalogo'
unzip -o ~/Downloads/muufeed_traducao_catalogo_patch.zip
python -m pytest -q
./init.sh
```

Reabra **Ingredientes e preços**. Os itens mostrados na captura enviada, como `Zinc, organic generic`, `Casein`, `Calf grower ...` e `Calf starter ...`, aparecem agora em português na coluna **Ingrediente**. A coluna **Nome original (NASEM)** permanecerá em inglês de propósito, para identificação inequívoca da base científica. A pesquisa aceita os dois idiomas.

## Abrangência e auditoria

Os 99 rótulos já cadastrados continuam sendo usados. Acrescentamos traduções explícitas adicionais e padrões seguros (por exemplo, sais minerais, aminoácidos protegidos e algumas forragens). O catálogo completo possui 284 itens; em caso de nome técnico sem correspondência segura, o nome original é preservado — não fazemos traduções automáticas aproximadas que poderiam identificar incorretamente um ingrediente.

Para auditar a cobertura efetiva na sua instalação:

```bash
python scripts/auditar_catalogo_pt.py
```

O script cria `traducoes_pendentes.csv` somente para revisão editorial. Não envie esse arquivo ao formulador e não substitua os nomes originais do NASEM.
