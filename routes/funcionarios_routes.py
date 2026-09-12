"""Rotas de funcionários: lista com filtro (só ativos), detalhe (com os
equipamentos sob a responsabilidade dele), editar, excluir (soft-delete) e
a tela de ver/restaurar excluídos."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from models import equipamento as equipamento_model
from models import funcionario as funcionario_model
from services import ServiceError
from services import funcionario_service

bp = Blueprint("funcionarios", __name__, url_prefix="/funcionarios")


def _funcionario_ou_404(id_):
    funcionario = funcionario_model.buscar_por_id(id_)
    if not funcionario:
        abort(404)
    return funcionario


@bp.route("/")
def listar():
    termo = request.args.get("busca", "")
    setor = request.args.get("setor", "")
    return render_template(
        "funcionarios.html",
        funcionarios=funcionario_model.listar(termo, setor),
        setores=funcionario_model.listar_setores(),
        termo=termo, setor=setor)


@bp.route("/excluidos")
def excluidos():
    return render_template("funcionarios_excluidos.html",
                          funcionarios=funcionario_model.listar_excluidos())


@bp.route("/<int:id_>")
def detalhe(id_):
    funcionario = _funcionario_ou_404(id_)
    return render_template(
        "funcionario_detalhe.html", funcionario=funcionario,
        equipamentos=equipamento_model.listar_por_responsavel(id_))


@bp.route("/<int:id_>/editar", methods=["GET", "POST"])
def editar(id_):
    funcionario = _funcionario_ou_404(id_)
    if request.method == "POST":
        dados = {
            "nome": request.form.get("nome", "").strip(),
            "setor": request.form.get("setor", "").strip() or None,
            "cargo": request.form.get("cargo", "").strip() or None,
            "email": request.form.get("email", "").strip() or None,
            "telefone": request.form.get("telefone", "").strip() or None,
        }
        try:
            funcionario_service.atualizar_funcionario(id_, dados)
            flash(f"{dados['nome']} atualizado.", "ok")
            return redirect(url_for("funcionarios.detalhe", id_=id_))
        except ServiceError as erro:
            flash(str(erro), "erro")
            funcionario = {**funcionario, **dados}
    return render_template("funcionario_editar.html", funcionario=funcionario)


@bp.route("/<int:id_>/excluir", methods=["POST"])
def excluir(id_):
    try:
        n_equipamentos = funcionario_service.excluir_funcionario(id_)
        aviso = ""
        if n_equipamentos:
            aviso = (f" Atenção: ele(a) ainda consta como responsável por "
                     f"{n_equipamentos} equipamento(s) — considere reatribuir.")
        flash(f"Funcionário excluído.{aviso}", "ok" if not n_equipamentos else "erro")
    except ServiceError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("funcionarios.listar"))


@bp.route("/<int:id_>/restaurar", methods=["POST"])
def restaurar(id_):
    try:
        funcionario_service.restaurar_funcionario(id_)
        flash("Funcionário restaurado.", "ok")
    except ServiceError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("funcionarios.excluidos"))
