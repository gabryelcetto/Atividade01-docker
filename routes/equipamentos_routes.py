"""Rotas de equipamentos — listagem única (todas as categorias, com filtro
opcional), substituindo as rotas antigas duplicadas /notebooks + /monitor.

O filtro de busca (?filtro=) nunca é usado direto numa query — é validado
contra FILTROS_PERMITIDOS em models/equipamento.py antes de qualquer coisa
(era aqui que existia o SQL injection do app.py antigo)."""
import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from models import equipamento as equipamento_model
from models import funcionario as funcionario_model
from services import ServiceError
from services import equipamento_service

bp = Blueprint("equipamentos", __name__, url_prefix="/equipamentos")


def _equipamento_ou_404(patrimonio):
    equipamento = equipamento_model.buscar_por_patrimonio(patrimonio)
    if not equipamento:
        abort(404)
    return equipamento


def _dados_do_form(form):
    return {
        "marca": form.get("marca", "").strip(),
        "modelo": form.get("modelo", "").strip(),
        "numero_serie": form.get("numero_serie", "").strip(),
        "endereco_mac": form.get("endereco_mac", "").strip(),
        "responsavel_nome": form.get("responsavel_nome", "").strip() or None,
        "setor": form.get("setor", "").strip() or None,
        "cargo": form.get("cargo", "").strip() or None,
        "sala": form.get("sala", "").strip() or None,
        "mesa": form.get("mesa", "").strip() or None,
        "status": form.get("status", "").strip(),
        "propriedade": form.get("propriedade", "Empresa"),
        "uso_externo": form.get("uso_externo") == "on",
        "data_compra": form.get("data_compra") or None,
        "garantia_meses": form.get("garantia_meses") or None,
        "observacao": form.get("observacao", "").strip(),
    }


@bp.route("/")
def listar():
    categorias = equipamento_model.listar_categorias()

    categoria_arg = request.args.get("categoria")
    if categoria_arg is None:
        # sem parâmetro na URL (ex.: acabou de clicar em "Equipamentos" no menu)
        # -> mostra Notebook por padrão. Ver tudo junto de cara ficava desorganizado;
        # "Todos" continua disponível como uma aba.
        notebook = next((c for c in categorias if c["nome"] == "Notebook"), None)
        categoria_id = notebook["id"] if notebook else None
    elif categoria_arg in ("", "todos"):
        categoria_id = None
    else:
        categoria_id = int(categoria_arg) if categoria_arg.isdigit() else None

    termo = request.args.get("busca", "")
    filtro = request.args.get("filtro", "")
    equipamentos = equipamento_model.listar(categoria_id, termo, filtro)
    return render_template(
        "index.html", equipamentos=equipamentos, categorias=categorias,
        categoria_id=categoria_id, termo=termo, filtro=filtro)


@bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        dados = _dados_do_form(request.form)
        dados["patrimonio"] = request.form.get("patrimonio", "").strip()
        dados["categoria_id"] = request.form.get("categoria_id", type=int)
        dados["data_cadastro"] = datetime.date.today().isoformat()

        if not dados["patrimonio"]:
            flash("Patrimônio é obrigatório.", "erro")
        elif not dados["categoria_id"]:
            flash("Categoria é obrigatória.", "erro")
        elif not dados["status"]:
            flash("Status é obrigatório.", "erro")
        else:
            try:
                equipamento_service.criar_equipamento(dados)
                flash(f"Equipamento {dados['patrimonio']} cadastrado.", "ok")
                return redirect(url_for("equipamentos.listar"))
            except ServiceError as erro:
                flash(str(erro), "erro")

    return render_template(
        "cadastro.html", categorias=equipamento_model.listar_categorias(),
        status_lista=equipamento_model.listar_status(),
        funcionarios=funcionario_model.listar())


@bp.route("/<patrimonio>/editar", methods=["GET", "POST"])
def editar(patrimonio):
    equipamento = _equipamento_ou_404(patrimonio)

    if request.method == "POST":
        dados = _dados_do_form(request.form)
        if not dados["status"]:
            flash("Status é obrigatório.", "erro")
        else:
            try:
                equipamento_service.atualizar_equipamento(patrimonio, dados)
                flash(f"Equipamento {patrimonio} atualizado.", "ok")
                return redirect(url_for("equipamentos.listar"))
            except ServiceError as erro:
                flash(str(erro), "erro")

    return render_template("editar.html", equipamento=equipamento,
                          status_lista=equipamento_model.listar_status(),
                          funcionarios=funcionario_model.listar())


@bp.route("/<patrimonio>/remover")
def remover(patrimonio):
    """Tela de confirmação com as duas opções: dar baixa (recomendado) ou
    excluir de vez (só pra corrigir cadastro errado)."""
    equipamento = _equipamento_ou_404(patrimonio)
    return render_template("excluir.html", equipamento=equipamento)


@bp.route("/<patrimonio>/baixa", methods=["POST"])
def baixa(patrimonio):
    _equipamento_ou_404(patrimonio)
    motivo = request.form.get("motivo", "").strip() or "Sem motivo informado."
    try:
        equipamento_service.dar_baixa_equipamento(patrimonio, motivo)
        flash(f"Equipamento {patrimonio} baixado.", "ok")
    except ServiceError as erro:
        flash(str(erro), "erro")
    return redirect(url_for("equipamentos.listar"))


@bp.route("/<patrimonio>/excluir", methods=["POST"])
def excluir(patrimonio):
    _equipamento_ou_404(patrimonio)
    try:
        equipamento_service.excluir_equipamento(patrimonio)
        flash(f"Equipamento {patrimonio} excluído.", "ok")
    except ServiceError as erro:
        flash(str(erro), "erro")
        return redirect(url_for("equipamentos.remover", patrimonio=patrimonio))
    return redirect(url_for("equipamentos.listar"))
