# syntax=docker/dockerfile:1

# ---- estágio 1: builder -----------------------------------------------------
# Instala as dependências Python isoladas do restante do sistema, pra não
# levar toolchain de build nenhuma pra imagem final.
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ---- estágio 2: runtime ------------------------------------------------------
FROM python:3.12-slim AS runtime

# Usuário não-root: a aplicação não precisa (e não deve) rodar como root.
RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

# Só os pacotes já instalados no builder, sem compilador/cache de pip.
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY . .
RUN mkdir -p static/uploads/fotos && chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
