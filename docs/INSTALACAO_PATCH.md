# Aplicação do pacote v6

1. Faça backup/commit no Git antes de instalar.
2. Baixe o ZIP `muufeed_v6_patch.zip` e descompacte na **raiz** do projeto; não copie o pacote para dentro de uma subpasta extra.
3. Execute o pytest e o smoke test do NASEM real.
4. Rode a interface via `./init.sh`.

```bash
cd ~/MuuFeed
git add . && git commit -m 'checkpoint antes do v6'
unzip -o ~/Downloads/muufeed_v6_patch.zip
python -m pytest -q
python scripts/verificar_nasem_minerais.py
./init.sh
```

Primeiro, teste a formulação **SEM marcar** a nova opção; o resultado deve ser comparável ao anterior. Depois marque `Exigir cálcio e fósforo ABSORVIDOS` e repita: o custo/dieta poderá mudar ou nenhuma candidata ser encontrada, o que revela possíveis limitações dos ingredientes disponíveis.

A documentação antiga pode ser inspecionada para exclusão usando `bash scripts/limpar_documentacao.sh` (somente prévia). Com backup já feito, execute `bash scripts/limpar_documentacao.sh --apply` se quiser removê-la.

## Limitações de validação deste pacote

Os testes unitários com avaliador simulado não substituem o teste real `nasem_dairy`. Só marque a integração mineral como validada após `verificar_nasem_minerais.py` retornar os campos absorvidos de Ca/P. Não elimine o aviso de dieta experimental.
