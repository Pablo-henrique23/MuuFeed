# MuuFeed v18 — seleção guiada por limites

**Base de instalação: v17.** Este ZIP contém arquivos alterados e novos, sem sobrepor a biblioteca NASEM.

```bash
cd ~/MuuFeed
git add . && git commit -m "checkpoint antes da selecao guiada v18"
unzip -o ~/Downloads/muufeed_v18_selecao_orientada_patch.zip
python -m pytest -q
python scripts/verificar_selecao_guiada_v18.py
./init.sh
```

Consulte `docs/SELECAO_ORIENTADA_V18.md` para modo de operação, referências, pressupostos e o cenário do júri.

No **modo guiado**, informe restrições antes da sugestão. O sistema filtra candidatos com composição e preços disponíveis, exclui aditivos de alto risco e testa quimicamente se eles podem satisfazer o limite de FDN/amido/FDNf/teto. A viabilidade de energia, proteína metabolizável e minerais **continua sendo verificada posteriormente pelo NASEM**. Confirme disponibilidade e preço de cada ingrediente e use teto individual para suplementos conforme supervisão profissional. A seleção guiada não promete uma dieta completa.

Se `python scripts/verificar_selecao_guiada_v18.py` acusar falha, não faça a demonstração do modo guiado até revisar os dados; use o modo manual validado.
