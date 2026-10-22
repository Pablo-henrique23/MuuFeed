# MuuFeed v14 — revisão de 284 ingredientes e segurança experimental

**Base de instalação:** versão v13 (patch `muufeed_v13_fdn_auditoria_patch.zip`). Não depende de outros ZIPs posteriores.

```bash
cd ~/MuuFeed
git add . && git commit -m "checkpoint antes do v14"
unzip -o ~/Downloads/muufeed_v14_auditoria_cientifica_patch.zip
python -m pytest -q
python scripts/auditar_catalogo_nutricional.py
./init.sh
```

## O que muda

- 5 alertas falsos/ambíguos resolvidos: `Alfalfa meal` é considerada forragem química segundo `Fd_Type`, apesar de categoria proteica, e `Fd_CP` >100% é permitido **somente** nas fontes NNP explicitamente reconhecidas.
- Auditoria 84 colunas por ingrediente (presença e integridade de tipo), 15 nutrientes com intervalo conhecido, NNP e classificações; CSV gerado novamente na máquina. **Não foram preenchidos dados químicos ausentes.**
- Com base na triagem 284 ingredientes enviada: **216 OK**, **68 com lacunas**, **0 pendências dos cinco alertas originais**, **77 forragens** e **207 não forragens**.
- **6 produtos exclusivos para bezerros** não são elegíveis para o formulador atual de vacas em lactação (ainda podem ser encontrados no catálogo).
- **Premixes minerais/vitamínicos, fontes NNP, aditivos e suplementos concentrados de gordura** precisam de máximo explícito informado pelo usuário no modelo antes de formular. O teto não é recomendado pelo sistema e não garante segurança.
- Anotações de estudos para exemplos com limites práticos, documentados como **referências condicionais, não como máximos automáticos**.

## Artefatos inclusos

- `docs/REVISAO_CIENTIFICA_CATALOGO_V14.md`: método e referências acadêmicas.
- `docs/auditoria_catalogo_revisada_v14.csv`: revisão do CSV **fornecido pelo usuário**; não altera o NASEM original.
- `docs/auditoria_catalogo_cientifica_v14.xlsx`: planilha de consulta com 284 itens, pendências e referências.

## Cuidado com o escopo

Auditamos os campos estruturais e de composição da biblioteca *de referência*, mas isso **não valida empiricamente** cada ração real nem fornece limites seguros para todos os 284 ingredientes. A qualidade depende do processamento, lote, água, armazenamento, contaminações e análise bromatológica. É incorreto declarar o catálogo 100% nutricionalmente certificado.

## Testes

Neste ambiente, passaram **182 testes** que independem de `nasem_dairy`, `streamlit` e `pyarrow`, incluindo novos casos v14. Os testes de integração real precisam ser repetidos na `.venv` do usuário.
