class ServiceError(Exception):
    """Erro esperado (validação de negócio) — a rota deve capturar e mostrar
    pro usuário via flash, sem stack trace."""
