"""Camada de serviço do mapa das salas.

O mapa é um documento só (abas de sala + blocos num canvas), guardado como
JSON numa linha da tabela `mapa_salas`. Substituiu a "planta em PowerPoint".

- `carregar()` devolve o layout já desserializado + o carimbo de tempo da
  última alteração (usado pra detectar edição concorrente).
- `salvar_layout()` valida forma e tamanho, checa se ninguém salvou por cima
  no meio-tempo (concorrência otimista) e grava numa transação.

Não sabe de Flask.
"""
import json

from banco import transacao
from models import mapa as mapa_model
from services import ServiceError

# 512 KB de JSON é MUITO mais que o suficiente (centenas de blocos). Serve só
# de teto de sanidade contra um payload absurdo.
TAMANHO_MAX_BYTES = 512 * 1024

CORES_VALIDAS = {0, 1, 2, 3}
TIPOS_VALIDOS = {"equip", "label", "mesa", "linha"}
FORMATOS_VALIDOS = {"notebook", "monitor", "fone", "generico"}
ROTACOES_VALIDAS = {0, 45, 90, 135, 180, 225, 270, 315}
GRADE_MIN, GRADE_MAX = 16, 120

LAYOUT_PADRAO = {
    "activeSala": 0,
    "grid": {"cols": 44, "rows": 28},
    "salas": [{"nome": "Sala 1", "cells": []}],
}


def carregar():
    linha = mapa_model.carregar()
    if not linha:
        return {"layout": LAYOUT_PADRAO, "atualizado_em": None}
    return {
        "layout": json.loads(linha["layout_json"]),
        "atualizado_em": linha["atualizado_em"].isoformat(timespec="seconds"),
    }


def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _validar(layout):
    if not isinstance(layout, dict):
        raise ServiceError("Formato de mapa inválido.")
    salas = layout.get("salas")
    if not isinstance(salas, list) or not salas:
        raise ServiceError("O mapa precisa de pelo menos uma sala.")
    if len(salas) > 50:
        raise ServiceError("Salas demais (máximo 50).")

    grade = layout.get("grid")
    if grade is not None:
        if not isinstance(grade, dict) \
           or not all(isinstance(grade.get(k), int) for k in ("cols", "rows")) \
           or not all(GRADE_MIN <= grade[k] <= GRADE_MAX for k in ("cols", "rows")):
            raise ServiceError("Tamanho de área inválido.")

    for sala in salas:
        if not isinstance(sala, dict):
            raise ServiceError("Formato de sala inválido.")
        if not isinstance(sala.get("nome"), str) or not sala["nome"].strip():
            raise ServiceError("Toda sala precisa de um nome.")
        if len(sala["nome"]) > 60:
            raise ServiceError("Nome de sala longo demais.")
        cells = sala.get("cells")
        if not isinstance(cells, list):
            raise ServiceError("Formato de blocos inválido.")
        if len(cells) > 400:
            raise ServiceError("Blocos demais numa sala (máximo 400).")
        for c in cells:
            if not isinstance(c, dict):
                raise ServiceError("Formato de bloco inválido.")
            if c.get("type") not in TIPOS_VALIDOS:
                raise ServiceError("Tipo de bloco inválido.")
            if c["type"] == "linha":
                if not all(_num(c.get(k)) and 0 <= c[k] <= 8000
                           for k in ("x1", "y1", "x2", "y2")):
                    raise ServiceError("Posição de linha inválida.")
                if "esp" in c and not (_num(c["esp"]) and 1 <= c["esp"] <= 80):
                    raise ServiceError("Espessura de linha inválida.")
            elif not all(_num(c.get(k)) for k in ("x", "y", "w", "h")):
                raise ServiceError("Posição/tamanho de bloco inválido.")
            for k in ("main", "sub", "id"):
                if k in c and not isinstance(c[k], str):
                    raise ServiceError("Conteúdo de bloco inválido.")
            for k in ("main", "sub"):
                if isinstance(c.get(k), str) and len(c[k]) > 120:
                    raise ServiceError("Texto de bloco longo demais.")
            if "colorIdx" in c and c["colorIdx"] not in CORES_VALIDAS:
                raise ServiceError("Cor de bloco inválida.")
            if "formato" in c and c["formato"] not in FORMATOS_VALIDOS:
                raise ServiceError("Formato de bloco inválido.")
            if "rotacao" in c and c["rotacao"] not in ROTACOES_VALIDAS:
                raise ServiceError("Rotação de bloco inválida.")


def salvar_layout(layout, base_atualizado_em=None):
    """Grava o layout. `base_atualizado_em` é o carimbo que o cliente carregou;
    se o mapa já mudou desde então, levanta ServiceError('CONFLITO')."""
    _validar(layout)

    texto = json.dumps(layout, ensure_ascii=False, separators=(",", ":"))
    if len(texto.encode("utf-8")) > TAMANHO_MAX_BYTES:
        raise ServiceError("O mapa ficou grande demais para salvar.")

    # Concorrência otimista: se já existe mapa salvo, o carimbo que o cliente
    # carregou tem que bater com o do banco. Se o cliente acha que ainda não
    # existe mapa (base None) mas já existe, também é conflito.
    atual = mapa_model.carregar()
    if atual is not None:
        carimbo_atual = atual["atualizado_em"].isoformat(timespec="seconds")
        if base_atualizado_em != carimbo_atual:
            raise ServiceError("CONFLITO")

    with transacao() as cursor:
        mapa_model.salvar(cursor, texto)

    return carregar()["atualizado_em"]


def _quando_texto(dt):
    return dt.strftime("%d/%m/%Y %H:%M")


def listar_versoes():
    return [
        {"id": v["id"], "quando": _quando_texto(v["salvo_em"])}
        for v in mapa_model.listar_historico()
    ]


def restaurar_versao(historico_id, base_atualizado_em=None):
    """Volta o mapa pra uma versão do histórico. O estado atual vai pro
    histórico antes (então dá pra desfazer a restauração também)."""
    versao = mapa_model.buscar_versao(historico_id)
    if not versao:
        raise ServiceError("Versão não encontrada.")

    try:
        layout = json.loads(versao["layout_json"])
    except (ValueError, TypeError):
        raise ServiceError("Essa versão está corrompida e não pode ser restaurada.")

    # mesma checagem de concorrência do salvar
    atual = mapa_model.carregar()
    if atual is not None:
        carimbo_atual = atual["atualizado_em"].isoformat(timespec="seconds")
        if base_atualizado_em is not None and base_atualizado_em != carimbo_atual:
            raise ServiceError("CONFLITO")

    _validar(layout)
    with transacao() as cursor:
        mapa_model.salvar(
            cursor, json.dumps(layout, ensure_ascii=False, separators=(",", ":")))
    return carregar()
