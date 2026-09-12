from flask import Flask, flash, redirect, render_template, request, url_for

from config import Config
from routes.dashboard_routes import bp as dashboard_bp
from routes.equipamentos_routes import bp as equipamentos_bp
from routes.fotos_routes import bp as fotos_bp
from routes.funcionarios_routes import bp as funcionarios_bp
from routes.mapa_routes import bp as mapa_bp
from routes.ocorrencias_routes import bp as ocorrencias_bp


def criar_app():
    """Application factory — cria e configura a aplicação Flask."""
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(equipamentos_bp)
    app.register_blueprint(funcionarios_bp)
    app.register_blueprint(ocorrencias_bp)
    app.register_blueprint(fotos_bp)
    app.register_blueprint(mapa_bp)

    @app.route("/")
    def inicial():
        return render_template("cover.html")

    @app.context_processor
    def injetar_nav_ativo():
        """Qual item do menu lateral fica destacado, calculado a partir da
        rota atual — assim nenhuma rota precisa passar isso manualmente."""
        endpoint = request.endpoint or ""
        if endpoint.startswith("equipamentos.cadastro"):
            nav = "cadastro"
        elif endpoint.startswith("equipamentos.") or endpoint.startswith("fotos."):
            nav = "equipamentos"
        elif endpoint.startswith("funcionarios."):
            nav = "funcionarios"
        elif endpoint.startswith("ocorrencias."):
            nav = "ocorrencias"
        elif endpoint.startswith("dashboard."):
            nav = "dashboard"
        elif endpoint.startswith("mapa."):
            nav = "mapa"
        else:
            nav = None
        return {"nav_ativo": nav}

    @app.context_processor
    def injetar_helpers():
        def url_foto(caminho_arquivo):
            """Monta a URL de exibição de uma foto. Se `caminho_arquivo` já é
            uma URL (foto no bucket S3), usa direto; senão é um caminho relativo
            à static/ (foto no disco local)."""
            if caminho_arquivo.startswith(("http://", "https://")):
                return caminho_arquivo
            return url_for("static", filename=caminho_arquivo)
        return {"url_foto": url_foto}

    @app.errorhandler(413)
    def arquivo_grande_demais(_erro):
        flash("Arquivo muito grande (máximo 25 MB).", "erro")
        return redirect(request.referrer or url_for("dashboard.inicio")), 413

    return app


app = criar_app()

# garante que o servidor seja ligado apenas se executar esse arquivo diretamente.
if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])
