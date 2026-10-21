# MuuFeed

Sistema especialista para formulação de dietas para bovinos leiteiros (hackathon). Execução 100% local.

Requer **Python 3.12** (o `nasem_dairy` exige NumPy 1.x).

```bash
pip install -r requirements.txt
streamlit run app.py          # abre em http://localhost:8501
python -m pytest -q           # testes
```
Documentação da interface e de como conectar o formulador: `docs/INTERFACE.md`.
