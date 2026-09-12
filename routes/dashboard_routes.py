"""Dashboard — visão geral do parque de equipamentos."""
from flask import Blueprint, render_template

from models import dashboard as dashboard_model

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.route("/")
def inicio():
    resumo, movimentacoes = dashboard_model.carregar()
    return render_template(
        "dashboard.html",
        resumo=resumo,
        movimentacoes=movimentacoes,
    )
