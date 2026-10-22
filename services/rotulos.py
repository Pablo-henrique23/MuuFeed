"""Rótulos legíveis para identificadores técnicos que o formulador devolve (ex.: `fibra_fisicamente_efetiva`).

Só apresentação: não altera o resultado nem a lógica nutricional. Sem Streamlit.
Para um requisito/restrição novo, acrescente a chave em `ROTULOS`; sem entrada, usa-se uma regra de reserva.
"""
from __future__ import annotations

import re
import unicodedata

from models import ResultadoFormulacao

ROTULOS = {
    "total_ms": "Consumo total de matéria seca (MS)",
    "me": "Energia metabolizável (ME)",
    "mp": "Proteína metabolizável (MP)",
    "limites_operacionais": "Limites mínimo/máximo informados pelo usuário",
    "fdn": "Fibra em detergente neutro (FDN)",
    "fdn_forragens": "FDN proveniente de forragens",
    "fibra_fisicamente_efetiva": "Fibra fisicamente efetiva",
    "amido": "Amido",
    "minerais": "Minerais",
    "calcio_absorvido": "Cálcio absorvido (NASEM)",
    "fosforo_absorvido": "Fósforo absorvido (NASEM)",
    "vitaminas": "Vitaminas",
    "limites_nutricionais_de_inclusao": "Limites nutricionais de inclusão de ingredientes",
}
_CHAVE = re.compile(r"[a-z][a-z0-9]*(_[a-z0-9]+)+")


def eh_chave_tecnica(texto: str) -> bool:
    """True para chaves de máquina (`total_ms`, `FDN`/`ME` conhecidas); False para códigos como `C1` ou frases."""
    t = str(texto).strip()
    return t.lower() in ROTULOS or bool(_CHAVE.fullmatch(t.lower()) and re.fullmatch(r"[A-Za-z0-9_]+", t))


def rotulo_legivel(texto: str) -> str:
    t = str(texto).strip()
    if t.lower() in ROTULOS:
        return ROTULOS[t.lower()]
    if eh_chave_tecnica(t):  # chave desconhecida: "limite_de_gordura" -> "Limite de gordura"
        s = t.lower().replace("_", " ")
        return s[0].upper() + s[1:]
    return t


def _chave(texto: str) -> str:
    s = unicodedata.normalize("NFKD", rotulo_legivel(texto)).encode("ascii", "ignore").decode()
    return " ".join(s.casefold().replace("_", " ").split())


def nao_avaliadas_unicas(res: ResultadoFormulacao) -> list[tuple[str, str]]:
    """Une restrições `nao_avaliada` e a lista `nao_avaliadas` numa única lista (rótulo, detalhe), sem repetição."""
    vistos: dict[str, tuple[str, str]] = {}
    for r in res.restricoes:
        if r.status == "nao_avaliada":
            vistos.setdefault(_chave(r.descricao or r.id), (rotulo_legivel(r.descricao or r.id), r.detalhe or ""))
    for t in res.nao_avaliadas:
        vistos.setdefault(_chave(t), (rotulo_legivel(t), ""))
    return list(vistos.values())
