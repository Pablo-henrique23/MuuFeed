# Correção do teste de integração PDF da v19

Esta correção atualiza somente `tests/test_integracao_nasem.py` para verificar o PDF sem a faixa vermelha removida na v19. O código do programa, cálculo nutricional e visual do PDF não são modificados.

## Aplicação (na raiz do projeto)

```bash
unzip -o ~/Downloads/muufeed_v19_correcao_teste_integracao_pdf.zip
python -m pytest -q
python scripts/verificar_hipoteses_nasem_v19.py
```

Se o script estiver em outro local na sua instalação, ajuste o caminho.
