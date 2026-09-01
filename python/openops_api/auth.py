"""
openops_api.auth
=================

Integração HTTP da autenticação: extrai o Bearer token do header
`Authorization`, delega a verificação para `openops_core.auth`, e expõe
`require_role(...)` como dependência do FastAPI para proteger rotas por
papel mínimo.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, status
from pydantic import BaseModel

from openops_core.auth import AuthService, TokenPayload, ROLE_LEVELS
from openops_core.errors import AuthorizationError

router = APIRouter(prefix="/auth", tags=["auth"])


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
    authorization: str | None = Header(default=None),
) -> TokenPayload:
    """Dependência do FastAPI: exige um `Authorization: Bearer <token>`
    válido. Qualquer rota que dependa disto exige, no mínimo, estar
    autenticado — não importa o papel.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthorizationError("token de autenticação ausente ou mal formatado")

    token = authorization.removeprefix("Bearer ").strip()
    return _auth_service(request).decode_token(token)


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
