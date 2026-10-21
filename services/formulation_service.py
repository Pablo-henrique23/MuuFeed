"""Ponto único de integração entre a interface e o formulador real.

Como conectar o formulador (ver docs/INTERFACE.md):
  1. Implemente uma classe com `verificar_escopo(req)` e `formular(req)` (protocolo `Formulador`).
  2. Aponte para ela:  set MUUFEED_FORMULADOR=meu_pacote.modulo:MinhaClasse   (ou chame `registrar_formulador`).
A interface não muda.
"""
from __future__ import annotations

import hashlib
import importlib
import json
import logging
import os
from datetime import datetime
from typing import Optional, Protocol

from models import STATUS_VALIDOS, RequisicaoFormulacao, ResultadoFormulacao

log = logging.getLogger("muufeed")


class Formulador(Protocol):
    def verificar_escopo(self, req: RequisicaoFormulacao) -> tuple[bool, str]: ...
    def formular(self, req: RequisicaoFormulacao) -> ResultadoFormulacao: ...


class FormuladorNaoConectado:
    """Padrão enquanto o motor real não existe. Não calcula nem inventa nada."""
    nome = "nenhum"

    def verificar_escopo(self, req):
        return True, ""

    def formular(self, req):
        return ResultadoFormulacao(
            status="nao_conectado",
            mensagem="O formulador ainda não está conectado. Nenhuma dieta foi calculada.",
            nao_avaliadas=["Todas as exigências e restrições nutricionais"],
        )


_registrado: Optional[Formulador] = None


def registrar_formulador(f: Optional[Formulador]) -> None:
    global _registrado
    _registrado = f


def carregar_formulador() -> Formulador:
    if _registrado is not None:
        return _registrado
    destino = os.environ.get("MUUFEED_FORMULADOR", "").strip()
    if destino:
        modulo, _, classe = destino.partition(":")
        return getattr(importlib.import_module(modulo), classe)()
    return FormuladorNaoConectado()


def formulador_conectado() -> bool:
    return not isinstance(carregar_formulador(), FormuladorNaoConectado)


def _identificar(res: ResultadoFormulacao, req: RequisicaoFormulacao) -> ResultadoFormulacao:
    if not res.id_formulacao:
        agora = datetime.now().astimezone()
        h = hashlib.sha1(json.dumps(req.to_dict(), sort_keys=True, default=str).encode()).hexdigest()[:6].upper()
        res.id_formulacao = f"MF-{agora:%Y%m%d-%H%M%S}-{h}"
        res.executada_em = agora.isoformat(timespec="seconds")
    return res


def executar_formulacao(req: RequisicaoFormulacao) -> ResultadoFormulacao:
    return _identificar(_executar(req), req)


def _executar(req: RequisicaoFormulacao) -> ResultadoFormulacao:
    try:
        f = carregar_formulador()
        ok, motivo = f.verificar_escopo(req)
        if not ok:
            return ResultadoFormulacao(status="escopo_nao_suportado",
                                       mensagem=motivo or "Categoria fora do escopo suportado.")
        res = f.formular(req)
        if res.status not in STATUS_VALIDOS:
            raise ValueError(f"status inválido devolvido pelo formulador: {res.status!r}")
        return res
    except Exception as exc:  # a interface nunca deve quebrar por falha do núcleo
        log.exception("Falha na formulação")
        return ResultadoFormulacao(status="erro", mensagem=f"Falha ao formular: {exc}")
