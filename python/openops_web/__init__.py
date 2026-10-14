# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""OpenOps Web — micro-site HTML para operar estoque, produtos, clientes e
usuários sem conhecimento de programação. Só biblioteca padrão do Python.
"""

from .app import WebApp, Request, Response, __version__
from .server import make_server, serve

__all__ = ["WebApp", "Request", "Response", "make_server", "serve", "__version__"]
