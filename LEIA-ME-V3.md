# MuuFeed — Motor v3: robustez e diagnóstico

Patch incremental baseado no MuuFeed integrado v2 + Fluxo Assistido + correção do PDF.

## Modificado
- `formulation_engine.py`: registra tentativas, convergência, custos de candidatas verificadas, diferenças da melhor tentativa não factível; emite alertas descritivos quando um ingrediente representa >=70% da MS ou ME >=120% da exigência. **Esses números são gatilhos de auditoria, NÃO limites nutricionais.** Não se adicionaram novas restrições.
- `services/nasem_adapter.py`: passa a usar 4 pontos iniciais e 100 iterações, propaga diagnóstico resumido e alertas aos avisos já apresentados na interface/PDF. Falha continua sem afirmar inviabilidade comprovada.
- `tests/test_motor_v3_diagnosticos.py`: dois testes com avaliador sintético.
- `BACKLOG_MUUFEED_COMPLETO.md`: lista consolidada.

## Instalação
Execute na raiz do MuuFeed:

```bash
git add . && git commit -m 'checkpoint antes do motor v3'
unzip -o ~/Downloads/muufeed_v3_diagnostico_patch.zip
python -m pytest -q
MUUFEED_FORMULADOR=services.nasem_adapter:NasemFormulador streamlit run app.py
```

## O que verificar
Use o lote 'teste fluxo 2' com os mesmos ingredientes e preços. Compare custos e proporções com os anteriores. Em avisos, espere `Diagnóstico SLSQP:` e, dependendo da composição, alertas `Composição concentrada:` e `Energia calculada em:`. Custos podem mudar porque aumentamos o número de partidas. O motor continua experimental e não garante ótimo global.

A suíte integral precisa ser executada no ambiente com Streamlit e nasem_dairy instalados. Testes sintéticos e de contrato são executáveis sem essas dependências.

**Idade:** 833 dias no relatório não é necessariamente erro do sistema: o Streamlit recebe idade em anos ou meses, e 2,28 anos x 365,25 = 832,77 dias. O exemplo NASEM anterior usava 820,8 dias, equivalente a cerca de 2,247 anos; ao arredondar 2,25 anos, obtém-se 821,81 dias. Informe/comunique esse arredondamento na apresentação.
