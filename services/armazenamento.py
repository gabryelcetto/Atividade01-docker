"""Onde as fotos dos equipamentos ficam guardadas.

Dois backends, escolhidos pela configuração (`de_config`):

* `ArmazenamentoLocal` — grava no disco, dentro de `static/`. É o padrão
  enquanto o `.env` não tiver as chaves do bucket. Serve pra desenvolver e pra
  rodar offline (ex.: o app empacotado como .exe numa máquina sem internet).

* `ArmazenamentoS3` — grava num "object storage" compatível com S3
  (Cloudflare R2, Backblaze B2, MinIO...). É o modo de produção: bancos
  gerenciados no tier gratuito costumam ter pouco espaço (ordem de 1 GB),
  então imagem não vai pra lá — vai pro bucket, e o banco guarda só a
  URL/chave.

Este módulo não sabe nada de Flask. Quem tem `current_app` (a rota) passa os
valores de configuração já resolvidos.

O que vai pra coluna `fotos.caminho_arquivo`:
  - local: caminho relativo à pasta `static/` (ex. `uploads/fotos/NB0210/<uuid>.jpg`)
  - S3:    a URL pública completa (ex. `https://pub-xxx.r2.dev/NB0210/<uuid>.jpg`)
O template usa o helper `url_foto()` (em app.py) que diferencia os dois pelo
"http" no começo.
"""
import os
import uuid


class ErroArmazenamento(Exception):
    """Falha ao gravar/apagar o arquivo no armazenamento."""


def _nome_unico(extensao):
    return f"{uuid.uuid4().hex}.{extensao}"


class ArmazenamentoLocal:
    modo = "local"

    def __init__(self, pasta_static, subpasta_uploads):
        # pasta_static: caminho absoluto da pasta static/ do Flask
        # subpasta_uploads: config PASTA_UPLOADS (ex. "uploads/fotos")
        self._subpasta = subpasta_uploads.replace(os.sep, "/").strip("/")
        self._raiz_fs = os.path.join(
            pasta_static, *self._subpasta.split("/"))

    def salvar(self, prefixo, extensao, dados, _content_type):
        nome = _nome_unico(extensao)
        pasta = os.path.join(self._raiz_fs, *prefixo.split("/"))
        os.makedirs(pasta, exist_ok=True)
        caminho_absoluto = os.path.join(pasta, nome)
        try:
            with open(caminho_absoluto, "wb") as saida:
                saida.write(dados)
        except OSError as erro:
            raise ErroArmazenamento(str(erro)) from erro
        # o que vai pro banco: relativo à static/
        return f"{self._subpasta}/{prefixo}/{nome}"

    def remover(self, referencia_no_banco):
        # referencia_no_banco ex.: "uploads/fotos/NB0210/<uuid>.jpg"
        caminho_absoluto = os.path.join(
            self._raiz_fs,
            *referencia_no_banco.split("/")[len(self._subpasta.split("/")):])
        if os.path.exists(caminho_absoluto):
            try:
                os.remove(caminho_absoluto)
            except OSError:
                pass


class ArmazenamentoS3:
    modo = "s3"

    def __init__(self, endpoint, bucket, access_key, secret_key, region,
                 base_url_publica):
        import boto3
        from botocore.config import Config as BotoConfig

        self._bucket = bucket
        self._base_url = base_url_publica.rstrip("/")
        self._cliente = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region or "auto",
            config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3}),
        )

    def salvar(self, prefixo, extensao, dados, content_type):
        chave = f"{prefixo}/{_nome_unico(extensao)}"
        try:
            self._cliente.put_object(
                Bucket=self._bucket, Key=chave, Body=dados,
                ContentType=content_type or "application/octet-stream",
                # nome do arquivo é uuid e nunca muda -> navegador/CDN podem
                # cachear pra sempre. Isso derruba quase a zero as "operações
                # Classe B" (downloads) em quem revisita a tela de fotos.
                CacheControl="public, max-age=31536000, immutable")
        except Exception as erro:  # boto3/botocore levantam vários tipos
            raise ErroArmazenamento(str(erro)) from erro
        return f"{self._base_url}/{chave}"

    def remover(self, referencia_no_banco):
        # referencia_no_banco é a URL pública completa -> extrai a chave
        if not referencia_no_banco.startswith(self._base_url):
            return
        chave = referencia_no_banco[len(self._base_url):].lstrip("/")
        try:
            self._cliente.delete_object(Bucket=self._bucket, Key=chave)
        except Exception:
            pass


def de_config(config, pasta_static):
    """Recebe o `current_app.config` (ou qualquer mapping equivalente) e o
    caminho absoluto da pasta static/. Devolve o backend certo."""
    usar_s3 = config.get("S3_BUCKET") and config.get("S3_ACCESS_KEY") \
        and config.get("S3_SECRET_KEY") and config.get("S3_ENDPOINT") \
        and config.get("S3_PUBLIC_BASE_URL")

    if usar_s3:
        return ArmazenamentoS3(
            endpoint=config["S3_ENDPOINT"],
            bucket=config["S3_BUCKET"],
            access_key=config["S3_ACCESS_KEY"],
            secret_key=config["S3_SECRET_KEY"],
            region=config.get("S3_REGION", "auto"),
            base_url_publica=config["S3_PUBLIC_BASE_URL"],
        )

    return ArmazenamentoLocal(pasta_static, config["PASTA_UPLOADS"])
