"""Testes baseados em propriedades do modelo de Cliente — foco no
validador de e-mail, que é exatamente o tipo de função propensa a
"passar" em todos os exemplos manuais e falhar num caso não previsto.
"""

from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from openops_business.customers.models import Customer
from openops_core.errors import ValidationError

valid_names = st.text(min_size=1, max_size=100).filter(lambda s: s.strip() != "")

# Gerador de e-mails plausivelmente válidos: local@dominio.tld
local_parts = st.text(alphabet=st.characters(whitelist_categories=["L", "N"]), min_size=1, max_size=20)
domain_parts = st.text(alphabet=st.characters(whitelist_categories=["L", "N"]), min_size=1, max_size=20)
tlds = st.sampled_from(["com", "com.br", "org", "net", "io"])


@given(
    name=valid_names,
    local=local_parts,
    domain=domain_parts,
    tld=tlds,
)
def test_any_wellformed_email_is_accepted(name, local, domain, tld):
    """Para QUALQUER e-mail no formato local@dominio.tld (com caracteres
    alfanuméricos), a criação nunca é rejeitada.
    """
    email = f"{local}@{domain}.{tld}"

    customer = Customer(name=name, email=email)

    assert customer.email == email


@given(name=valid_names, text_without_at=st.text(min_size=1, max_size=50).filter(lambda s: "@" not in s))
def test_email_without_at_sign_is_always_rejected(name, text_without_at):
    """Para QUALQUER string sem '@', usá-la como e-mail é sempre
    rejeitado.
    """
    with pytest.raises(ValidationError):
        Customer(name=name, email=text_without_at)


@given(name=valid_names, local=local_parts, domain_no_dot=domain_parts)
def test_email_with_domain_without_dot_is_always_rejected(name, local, domain_no_dot):
    """Para QUALQUER domínio sem ponto (ex.: 'algo@dominiosemtld'), a
    validação sempre rejeita — não existe TLD sem separador.
    """
    email = f"{local}@{domain_no_dot}"

    with pytest.raises(ValidationError):
        Customer(name=name, email=email)
