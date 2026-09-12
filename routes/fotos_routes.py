"""Rotas de upload/listagem/remoção de fotos de um equipamento.

Não estava na lista de arquivos do documento de arquitetura (só o
models/foto.py estava previsto) — criado como blueprint próprio pelo mesmo
motivo de ocorrencias_routes.py: manter equipamentos_routes.py enxuto.

Onde a imagem é gravada (disco local x bucket S3) é decidido em
services/armazenamento.py a partir da config; a rota só monta o objeto e
passa as travas de limite (config) pro serviço.
"""
from flask import (Blueprint, abort, current_app, flash, redirect, render_template,
                   request, url_for)

from models import equipamento as equipamento_model
from models import foto as foto_model
from models import ocorrencia as ocorrencia_model
from services import ServiceError
from services import armazenamento as armazenamento_mod
from services import foto_service

bp = Blueprint("fotos", __name__, url_prefix="/equipamentos")


def _equipamento_ou_404(patrimonio):
    equipamento = equipamento_model.buscar_por_patrimonio(patrimonio)
    if not equipamento:
        abort(404)
    return equipamento


def _armazenamento():
    return armazenamento_mod.de_config(
        current_app.config, current_app.static_folder)


def _limites():
    cfg = current_app.config
    return {
        "max_arquivo_bytes": int(cfg["FOTO_MAX_MB"] * 1024 * 1024),
        "max_por_equipamento": cfg["FOTO_MAX_POR_EQUIPAMENTO"],
        "max_total_bytes": int(cfg["S3_LIMITE_GB"] * 1024 * 1024 * 1024),
    }


@bp.route("/<patrimonio>/fotos", methods=["GET", "POST"])
def listar(patrimonio):
    equipamento = _equipamento_ou_404(patrimonio)

    if request.method == "POST":
        tipo = request.form.get("tipo", "cadastro")
        ocorrencia_id_raw = request.form.get("ocorrencia_id") or None
        ocorrencia_id = int(ocorrencia_id_raw) if ocorrencia_id_raw else None
        arquivo = request.files.get("arquivo")

        try:
            foto_service.salvar_foto(
                _armazenamento(), patrimonio, arquivo, tipo, ocorrencia_id,
                **_limites())
            flash("Foto enviada.", "ok")
        except ServiceError as erro:
            flash(str(erro), "erro")
        return redirect(url_for("fotos.listar", patrimonio=patrimonio))

    usado_bytes = foto_model.total_bytes()
    teto_bytes = int(current_app.config["S3_LIMITE_GB"] * 1024 * 1024 * 1024)
    armazenamento_info = {
        "modo": _armazenamento().modo,
        "usado_mb": usado_bytes / (1024 * 1024),
        "teto_mb": teto_bytes / (1024 * 1024),
        "pct": (usado_bytes / teto_bytes * 100) if teto_bytes else 0,
    }

    return render_template(
        "fotos.html", equipamento=equipamento,
        fotos=foto_model.listar_por_equipamento(patrimonio),
        ocorrencias=ocorrencia_model.listar_por_equipamento(patrimonio),
        armazenamento_info=armazenamento_info)


@bp.route("/<patrimonio>/fotos/<int:foto_id>/excluir", methods=["POST"])
def excluir(patrimonio, foto_id):
    _equipamento_ou_404(patrimonio)
    try:
        foto_service.excluir_foto(_armazenamento(), foto_id)
        flash("Foto removida.", "ok")
    except ServiceError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("fotos.listar", patrimonio=patrimonio))
