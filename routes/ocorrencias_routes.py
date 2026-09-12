"""Rotas de ocorrências (registro de problema/manutenção de um equipamento).

Quem relata e quem resolve são escolhidos numa lista de funcionários já
cadastrados (select), não texto livre — diferente do campo "responsável" do
equipamento, aqui faz mais sentido apontar pra alguém que já existe."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from models import equipamento as equipamento_model
from models import funcionario as funcionario_model
from models import ocorrencia as ocorrencia_model
from services import ServiceError
from services import ocorrencia_service

bp = Blueprint("ocorrencias", __name__, url_prefix="/ocorrencias")


def _equipamento_ou_404(patrimonio):
    equipamento = equipamento_model.buscar_por_patrimonio(patrimonio)
    if not equipamento:
        abort(404)
    return equipamento


def _ocorrencia_ou_404(id_):
    ocorrencia = ocorrencia_model.buscar_por_id(id_)
    if not ocorrencia:
        abort(404)
    return ocorrencia


@bp.route("/")
def listar_abertas():
    return render_template("ocorrencias_lista.html",
                          ocorrencias=ocorrencia_model.listar_abertas())


@bp.route("/equipamento/<patrimonio>")
def por_equipamento(patrimonio):
    equipamento = _equipamento_ou_404(patrimonio)
    ocorrencias = ocorrencia_model.listar_por_equipamento(patrimonio)
    return render_template("ocorrencias_equipamento.html", equipamento=equipamento,
                          ocorrencias=ocorrencias)


@bp.route("/equipamento/<patrimonio>/nova", methods=["GET", "POST"])
def nova(patrimonio):
    equipamento = _equipamento_ou_404(patrimonio)
    if request.method == "POST":
        problema = request.form.get("problema_relatado", "").strip()
        descricao = request.form.get("descricao", "").strip() or None
        funcionario_id_raw = request.form.get("funcionario_id") or None
        funcionario_id = int(funcionario_id_raw) if funcionario_id_raw else None
        muda_status_para = request.form.get("muda_status_para") or None

        if not problema:
            flash("Descreva o problema relatado.", "erro")
        else:
            try:
                ocorrencia_service.abrir_ocorrencia(
                    patrimonio, funcionario_id, problema, descricao, muda_status_para)
                flash("Ocorrência aberta.", "ok")
                return redirect(url_for("ocorrencias.por_equipamento", patrimonio=patrimonio))
            except ServiceError as erro:
                flash(str(erro), "erro")

    return render_template("ocorrencia_nova.html", equipamento=equipamento,
                          funcionarios=funcionario_model.listar(),
                          status_lista=equipamento_model.listar_status())


@bp.route("/<int:id_>/resolver", methods=["GET", "POST"])
def resolver(id_):
    ocorrencia = _ocorrencia_ou_404(id_)
    if request.method == "POST":
        solucao = request.form.get("solucao_aplicada", "").strip()
        tecnico_id_raw = request.form.get("tecnico_id") or None
        tecnico_id = int(tecnico_id_raw) if tecnico_id_raw else None
        novo_status = request.form.get("novo_status_equipamento") or None

        if not solucao:
            flash("Descreva a solução aplicada.", "erro")
        else:
            try:
                ocorrencia_service.resolver_ocorrencia(id_, solucao, tecnico_id, novo_status)
                flash("Ocorrência resolvida.", "ok")
                return redirect(url_for("ocorrencias.por_equipamento",
                                        patrimonio=ocorrencia["equipamento_patrimonio"]))
            except ServiceError as erro:
                flash(str(erro), "erro")

    return render_template("ocorrencia_resolver.html", ocorrencia=ocorrencia,
                          funcionarios=funcionario_model.listar(),
                          status_lista=equipamento_model.listar_status())
