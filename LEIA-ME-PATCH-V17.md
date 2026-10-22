# Patch MuuFeed v17 — transparência das candidatas e revisão do PDF

Base: **v16**, sem instalar versões intermediárias.

## Alterações
- No resultado Streamlit, retirada a legenda redundante sobre preço/kg MN e soma da coluna de custos.
- Na faixa vermelha de todas as páginas do PDF: `Candidata experimental - É necessária a revisão de um profissional`.
- No quadro inicial: título `Candidata experimental`; embaixo, somente `Resultado experimental: atende somente às restrições efetivamente verificadas. Não use para alimentar animais sem revisão de um profissional.`
- Restrições não avaliadas continuam visíveis na seção 6 e limitações na seção 8.
- Multistart do SLSQP: **6** pontos iniciais determinísticos, antes 4. O diagnóstico registra quantos pontos validados tiveram **composição distinta** (tolerância 0,001 kg MS), sem confundir pontos iniciais com novas dietas. O sistema exporta somente a candidata de menor custo, sem garantir ótimo global e sem impor variedade artificial.

## Instalação
```bash
cd ~/MuuFeed
git add . && git commit -m "checkpoint antes do patch v17"
unzip -o ~/Downloads/muufeed_v17_ux_pdf_multistart_patch.zip
python -m pytest -q
./init.sh
```

## Limitações preservadas
O cálculo nutricional não foi alterado, mas buscar com mais pontos iniciais pode retornar uma candidata diferente e requer mais avaliações, sem garantir maior diversidade. Limites operacionais percentuais não substituem limites nutricionais de inclusão nem a análise de especialista.
