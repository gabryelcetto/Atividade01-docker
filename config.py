import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuração da aplicação Flask (não confundir com banco.py, que resolve
    a conexão MySQL usando as mesmas variáveis de ambiente)."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-nao-use-em-producao")
    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

    # Caminhos de upload — sempre relativos à pasta static/ do Flask, nunca
    # absolutos (importante pra continuar funcionando dentro de um container).
    # Configuráveis por env var.
    PASTA_UPLOADS = os.getenv("PASTA_UPLOADS", os.path.join("uploads", "fotos"))
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB por upload

    # ---- Armazenamento de fotos ---------------------------------------------
    # Bancos gerenciados no tier gratuito costumam ter pouco espaço (ordem de
    # 1 GB) — foto não cabe lá. Então as imagens vão pra um "object storage"
    # compatível com S3 (Cloudflare R2 tem 10 GB grátis; Backblaze B2 também
    # serve). O banco guarda só a chave/URL da imagem.
    #
    # Enquanto essas variáveis não estiverem no .env, o app usa o disco local
    # (static/uploads/) — funciona pra desenvolver e pra rodar offline. Assim
    # que o .env tiver S3_BUCKET + chaves, ele passa a usar o bucket sozinho.
    S3_ENDPOINT = os.getenv("S3_ENDPOINT")            # ex.: https://<conta>.r2.cloudflarestorage.com
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY")
    S3_SECRET_KEY = os.getenv("S3_SECRET_KEY")
    S3_REGION = os.getenv("S3_REGION", "auto")
    # URL pública de leitura do bucket (R2: "Public Development URL" ou domínio
    # próprio). Sem "/" no fim.
    S3_PUBLIC_BASE_URL = (os.getenv("S3_PUBLIC_BASE_URL") or "").rstrip("/")

    # ---- Travas pra NUNCA sair do tier gratuito do R2 ----------------------
    # O grátis do R2 é: 10 GB de armazenamento, 1 milhão de uploads/mês,
    # 10 milhões de downloads/mês. O app impõe limites bem abaixo disso:
    #  - recusa upload se o total de fotos passar de S3_LIMITE_GB (default 8);
    #  - recusa arquivo maior que FOTO_MAX_MB;
    #  - recusa mais de FOTO_MAX_POR_EQUIPAMENTO fotos no mesmo equipamento.
    # Com isso o bucket não tem como crescer além do limite nem gerar cobrança.
    S3_LIMITE_GB = float(os.getenv("S3_LIMITE_GB", "8"))
    FOTO_MAX_MB = float(os.getenv("FOTO_MAX_MB", "10"))
    FOTO_MAX_POR_EQUIPAMENTO = int(os.getenv("FOTO_MAX_POR_EQUIPAMENTO", "15"))

    @staticmethod
    def usar_s3():
        return all([
            os.getenv("S3_ENDPOINT"), os.getenv("S3_BUCKET"),
            os.getenv("S3_ACCESS_KEY"), os.getenv("S3_SECRET_KEY"),
            os.getenv("S3_PUBLIC_BASE_URL"),
        ])
