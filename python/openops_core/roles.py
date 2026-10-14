# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""
openops_core.roles
===================

Papéis (RBAC) do OpenOps, em um módulo **sem dependências de terceiros**.
Ficam separados de ``openops_core.auth`` (que usa PyJWT e Argon2) para que
o micro-site (``openops_web``), que roda só com a biblioteca padrão do
Python, e a API FastAPI compartilhem exatamente a mesma definição de
privilégios — uma única fonte de verdade para "quem pode o quê".
"""

from __future__ import annotations

#: Ordem de privilégio — "viewer" só lê, "operator" também cria/edita/
#: apaga dados de negócio, "admin" acumula tudo e ainda gerencia usuários.
ROLE_LEVELS: dict[str, int] = {"viewer": 1, "operator": 2, "admin": 3}


def role_satisfies(user_role: str, minimum: str) -> bool:
    """Função pura: ``user_role`` tem privilégio suficiente para ``minimum``?"""
    return ROLE_LEVELS.get(user_role, 0) >= ROLE_LEVELS.get(minimum, 0)
