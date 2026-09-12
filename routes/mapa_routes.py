"""Mapa das salas — editor próprio (abas de sala + blocos arrastáveis num
canvas). Substituiu a planta em PowerPoint.

`GET  /mapa/`        -> a tela do editor (com o layout já embutido)
`GET  /mapa/layout`  -> o layout em JSON (pra recarregar sem F5)
`POST /mapa/layout`  -> salva o layout (JSON no corpo); 409 se houve edição
                        concorrente
"""
from flask import Blueprint, jsonify, render_template, request

from models import equipamento as equipamento_model
from services import ServiceError
from services import mapa_service

bp = Blueprint("mapa", __name__, url_prefix="/mapa")


@bp.route("/")
def ver():
    dados = mapa_service.carregar()
    return render_template(
        "mapa.html",
        layout=dados["layout"],
        atualizado_em=dados["atualizado_em"],
        equipamentos=equipamento_model.listar_para_mapa())


@bp.route("/layout", methods=["GET"])
def obter_layout():
    return jsonify(mapa_service.carregar())


@bp.route("/layout", methods=["POST"])
def salvar_layout():
    corpo = request.get_json(silent=True) or {}
    try:
        atualizado_em = mapa_service.salvar_layout(
            corpo.get("layout"), corpo.get("base_atualizado_em"))
    except ServiceError as erro:
        if str(erro) == "CONFLITO":
            return jsonify({"ok": False, "conflito": True}), 409
        return jsonify({"ok": False, "erro": str(erro)}), 400
    return jsonify({"ok": True, "atualizado_em": atualizado_em})


@bp.route("/versoes", methods=["GET"])
def versoes():
    return jsonify({"versoes": mapa_service.listar_versoes()})


@bp.route("/restaurar", methods=["POST"])
def restaurar():
    corpo = request.get_json(silent=True) or {}
    try:
        dados = mapa_service.restaurar_versao(
            corpo.get("id"), corpo.get("base_atualizado_em"))
    except ServiceError as erro:
        if str(erro) == "CONFLITO":
            return jsonify({"ok": False, "conflito": True}), 409
        return jsonify({"ok": False, "erro": str(erro)}), 400
    return jsonify({
        "ok": True, "layout": dados["layout"], "atualizado_em": dados["atualizado_em"]})
