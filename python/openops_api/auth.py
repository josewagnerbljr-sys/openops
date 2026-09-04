"""
openops_api.auth
=================

Integração HTTP da autenticação: extrai o Bearer token do header
`Authorization`, delega a verificação para `openops_core.auth`, e expõe
`require_role(...)` como dependência do FastAPI para proteger rotas por
papel mínimo.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from openops_core.auth import AuthService, TokenPayload, ROLE_LEVELS
from openops_core.errors import AuthorizationError

router = APIRouter(prefix="/auth", tags=["auth"])

#: `auto_error=False` porque queremos controlar nós mesmos a mensagem de
#: erro (via OpenOpsError -> resposta padronizada), não a mensagem
#: genérica que o FastAPI daria sozinho. Declarar isso como um esquema
#: de segurança "de verdade" (em vez de um Header cru) é o que faz o
#: Swagger UI mostrar o botão global "Authorize" 🔒 — sem isso, cada
#: rota mostra um campo de texto solto pedindo o header manualmente.
bearer_scheme = HTTPBearer(auto_error=False, description="Cole aqui o token JWT obtido em /auth/login")


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "viewer"


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    username: str
    role: str


def _auth_service(request: Request) -> AuthService:
    return request.app.state.auth_service


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenPayload:
    """Dependência do FastAPI: exige um Bearer token JWT válido. Qualquer
    rota que dependa disto exige, no mínimo, estar autenticado — não
    importa o papel.
    """
    if credentials is None or not credentials.credentials:
        raise AuthorizationError("token de autenticação ausente ou mal formatado")

    return _auth_service(request).decode_token(credentials.credentials)


def require_role(minimum: str):
    """Fábrica de dependência: `Depends(require_role("operator"))`
    exige, além de autenticado, papel "operator" ou superior.
    """
    if minimum not in ROLE_LEVELS:
        raise ValueError(f"papel mínimo desconhecido: {minimum!r}")

    def dependency(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if ROLE_LEVELS.get(user.role, 0) < ROLE_LEVELS[minimum]:
            raise AuthorizationError(
                f"esta operação exige papel '{minimum}' ou superior",
                details={"seu_papel": user.role, "papel_exigido": minimum},
            )
        return user

    return dependency


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, request: Request) -> UserOut:
    user = _auth_service(request).register(
        username=payload.username, password=payload.password, role=payload.role
    )
    return UserOut(username=user.username, role=user.role)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request) -> TokenResponse:
    token = _auth_service(request).authenticate(username=payload.username, password=payload.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: TokenPayload = Depends(get_current_user)) -> UserOut:
    return UserOut(username=user.username, role=user.role)
