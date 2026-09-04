"""
openops_api.security_demo
==========================

Playground público de criptografia — demonstra AES-256-GCM de verdade,
de forma interativa, para quem visita a API pela primeira vez sem
precisar criar conta. **Não tem relação nenhuma com o crate
`openops-security` (Rust)** usado no resto da arquitetura — é uma
reimplementação didática, isolada, em Python (via `cryptography`,
biblioteca madura e amplamente auditada), pensada só pra ensinar/
demonstrar, nunca pra proteger dado real do sistema.

Decisões de design que valem documentar:
- Cada chamada gera uma chave efêmera nova — nunca há uma "chave do
  sistema" envolvida aqui, então não existe segredo real a vazar.
- As rotas ficam FORA da autenticação (públicas de propósito): é uma
  vitrine, não uma capacidade de negócio.
"""

from __future__ import annotations

import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/security-demo", tags=["security-demo"])

KEY_SIZE_BYTES = 32  # AES-256
NONCE_SIZE_BYTES = 12  # 96 bits, padrão do GCM


class EncryptRequest(BaseModel):
    plaintext: str = Field(..., min_length=1, max_length=2000)


class EncryptResponse(BaseModel):
    plaintext: str
    key_hex: str
    nonce_hex: str
    ciphertext_hex: str
    explicacao: str


class DecryptRequest(BaseModel):
    key_hex: str
    nonce_hex: str
    ciphertext_hex: str


class DecryptResponse(BaseModel):
    sucesso: bool
    plaintext: str | None = None
    explicacao: str


class TamperDemoResponse(BaseModel):
    plaintext_original: str
    key_hex: str
    ciphertext_original_hex: str
    ciphertext_adulterado_hex: str
    byte_alterado_na_posicao: int
    decriptografia_do_original: DecryptResponse
    decriptografia_do_adulterado: DecryptResponse


@router.post("/encrypt", response_model=EncryptResponse)
def encrypt_demo(payload: EncryptRequest) -> EncryptResponse:
    """Cifra um texto com uma chave AES-256 gerada na hora (nunca
    armazenada, nunca reaproveitada). Devolve tudo em hexadecimal pra
    você poder colar direto em `/security-demo/decrypt` e ver o
    roundtrip funcionando.
    """
    key = os.urandom(KEY_SIZE_BYTES)
    nonce = os.urandom(NONCE_SIZE_BYTES)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, payload.plaintext.encode("utf-8"), associated_data=None)

    return EncryptResponse(
        plaintext=payload.plaintext,
        key_hex=key.hex(),
        nonce_hex=nonce.hex(),
        ciphertext_hex=ciphertext.hex(),
        explicacao=(
            "AES-256-GCM: uma cifra autenticada (AEAD). O 'ciphertext' já inclui "
            "a tag de autenticação nos últimos 16 bytes — qualquer adulteração, "
            "por menor que seja, faz a decriptografia falhar de propósito, em vez "
            "de devolver dado corrompido silenciosamente. Teste em /security-demo/tamper-demo."
        ),
    )


@router.post("/decrypt", response_model=DecryptResponse)
def decrypt_demo(payload: DecryptRequest) -> DecryptResponse:
    """Decifra um valor gerado por /encrypt. Se qualquer byte da chave,
    nonce ou ciphertext estiver errado, retorna sucesso=false — nunca
    lança um erro 500 nem devolve dado parcial.
    """
    try:
        key = bytes.fromhex(payload.key_hex)
        nonce = bytes.fromhex(payload.nonce_hex)
        ciphertext = bytes.fromhex(payload.ciphertext_hex)
    except ValueError:
        return DecryptResponse(
            sucesso=False,
            explicacao="Um dos campos não é hexadecimal válido — confira se copiou certinho.",
        )

    if len(key) != KEY_SIZE_BYTES:
        return DecryptResponse(
            sucesso=False,
            explicacao=f"Chave precisa ter {KEY_SIZE_BYTES} bytes (64 caracteres hex); recebido: {len(key)} bytes.",
        )

    try:
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
    except InvalidTag:
        return DecryptResponse(
            sucesso=False,
            explicacao=(
                "Falha de autenticação (InvalidTag) — o dado foi adulterado, ou a "
                "chave/nonce não correspondem a este ciphertext. Isso é o AEAD "
                "funcionando corretamente, não um bug."
            ),
        )

    return DecryptResponse(
        sucesso=True,
        plaintext=plaintext.decode("utf-8"),
        explicacao="Autenticação validada — o dado não foi adulterado desde que foi cifrado.",
    )


@router.post("/tamper-demo", response_model=TamperDemoResponse)
def tamper_demo(payload: EncryptRequest) -> TamperDemoResponse:
    """Demonstração guiada, num único passo: cifra o texto, corrompe
    UM byte do resultado de propósito, e mostra lado a lado a
    decriptografia do original (sucesso) vs. do adulterado (falha) —
    sem você precisar montar essa comparação manualmente.
    """
    key = os.urandom(KEY_SIZE_BYTES)
    nonce = os.urandom(NONCE_SIZE_BYTES)
    aesgcm = AESGCM(key)
    original_ciphertext = aesgcm.encrypt(nonce, payload.plaintext.encode("utf-8"), associated_data=None)

    tampered = bytearray(original_ciphertext)
    flip_index = len(tampered) // 2
    tampered[flip_index] ^= 0xFF
    tampered_ciphertext = bytes(tampered)

    original_result = decrypt_demo(
        DecryptRequest(key_hex=key.hex(), nonce_hex=nonce.hex(), ciphertext_hex=original_ciphertext.hex())
    )
    tampered_result = decrypt_demo(
        DecryptRequest(key_hex=key.hex(), nonce_hex=nonce.hex(), ciphertext_hex=tampered_ciphertext.hex())
    )

    return TamperDemoResponse(
        plaintext_original=payload.plaintext,
        key_hex=key.hex(),
        ciphertext_original_hex=original_ciphertext.hex(),
        ciphertext_adulterado_hex=tampered_ciphertext.hex(),
        byte_alterado_na_posicao=flip_index,
        decriptografia_do_original=original_result,
        decriptografia_do_adulterado=tampered_result,
    )


class QuizQuestion(BaseModel):
    pergunta: str
    opcoes: list[str]
    resposta_correta_index: int
    explicacao: str


class QuizResponse(BaseModel):
    titulo: str
    perguntas: list[QuizQuestion]


_QUIZ_QUESTIONS = [
    QuizQuestion(
        pergunta="O que significa o 'GCM' em AES-256-GCM?",
        opcoes=[
            "Galois/Counter Mode",
            "General Cryptographic Method",
            "Government Certified Module",
            "Global Cipher Manager",
        ],
        resposta_correta_index=0,
        explicacao="Galois/Counter Mode — combina criptografia em modo contador com autenticação baseada em campo de Galois, formando um AEAD.",
    ),
    QuizQuestion(
        pergunta="O que acontece se você reusar o mesmo nonce duas vezes com a mesma chave, no GCM?",
        opcoes=[
            "Nada, o nonce é só decorativo",
            "A confidencialidade é quebrada — um atacante pode recuperar informação",
            "A cifra fica mais rápida",
            "O sistema trava automaticamente",
        ],
        resposta_correta_index=1,
        explicacao="Reuso de nonce no GCM é uma das falhas mais graves possíveis — permite recuperar o XOR dos textos claros e forjar a tag de autenticação.",
    ),
    QuizQuestion(
        pergunta="Por que AES-256-GCM é chamado de 'cifra autenticada' (AEAD)?",
        opcoes=[
            "Porque exige login para usar",
            "Porque cifra e autentica (detecta adulteração) no mesmo passo",
            "Porque usa autenticação em dois fatores",
            "Porque é aprovado por um órgão de certificação",
        ],
        resposta_correta_index=1,
        explicacao="AEAD = Authenticated Encryption with Associated Data: garante confidencialidade E integridade juntas — qualquer alteração no ciphertext é detectada na decriptografia.",
    ),
    QuizQuestion(
        pergunta="Quantos bits tem uma chave AES-256?",
        opcoes=["128", "192", "256", "512"],
        resposta_correta_index=2,
        explicacao="O '256' no nome já indica: 256 bits = 32 bytes de chave.",
    ),
]


@router.get("/quiz", response_model=QuizResponse)
def get_quiz() -> QuizResponse:
    """Um quiz curto sobre os conceitos por trás do AES-256-GCM — pra
    quem quiser ir além de só ver a demo funcionando.
    """
    return QuizResponse(titulo="Quiz: AES-256-GCM na prática", perguntas=_QUIZ_QUESTIONS)
