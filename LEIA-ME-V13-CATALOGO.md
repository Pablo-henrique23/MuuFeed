# PATCH V13 — FDN de forragens + auditoria completa do catálogo

**Instalar SOBRE o MuuFeed v12 já testado**, sem baixar novamente nenhum dos
patches anteriores:

```bash
cd ~/MuuFeed
git add . && git commit -m "checkpoint antes do patch v13"
unzip -o ~/Downloads/muufeed_v13_fdn_auditoria_patch.zip
python -m pytest -q
python scripts/auditar_catalogo_nutricional.py
./init.sh
```

A auditoria gera `auditoria_catalogo_nasem.csv` na raiz do repositório.
Se houver `REVISAO_NECESSARIA`, envie esse CSV e a saída do terminal antes da
apresentação. Nutrição ausente não é substituída por zero nem inventada.

Detalhes: `docs/VALIDACAO_CATALOGO_V13.md`.
