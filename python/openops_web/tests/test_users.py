# AI assistance (CS50 final-project policy): this file was written or modified with the AI assistant Claude (Anthropic). See README.md, section 6.
"""Regras de negócio dos usuários do micro-site."""

import pytest

from openops_core.db import Database
from openops_core.errors import AuthorizationError, ConflictError, ValidationError
from openops_web.users import UserStore


@pytest.fixture
def store():
    return UserStore(Database(":memory:"))


def test_first_admin_only_once(store):
    store.create_first_admin(username="jose", password="senha-forte-1")

    with pytest.raises(ConflictError):
        store.create_first_admin(username="outro", password="senha-forte-1")


def test_username_is_case_insensitive_unique(store):
    store.create(username="Maria", password="senha-forte-1")

    with pytest.raises(ConflictError):
        store.create(username="maria", password="senha-forte-1")


@pytest.mark.parametrize("bad", ["ab", "x" * 33, "com espaço", "a;b", "<script>", ""])
def test_invalid_usernames_are_rejected(store, bad):
    with pytest.raises(ValidationError):
        store.create(username=bad, password="senha-forte-1")


def test_invalid_role_is_rejected(store):
    with pytest.raises(ValidationError):
        store.create(username="maria", password="senha-forte-1", role="superuser")


def test_authenticate_success_and_failure_are_indistinguishable(store):
    store.create(username="maria", password="senha-forte-1")

    assert store.authenticate(username="maria", password="senha-forte-1").username == "maria"
    with pytest.raises(AuthorizationError) as wrong_password:
        store.authenticate(username="maria", password="errada-errada")
    with pytest.raises(AuthorizationError) as unknown_user:
        store.authenticate(username="ninguem", password="errada-errada")

    assert str(wrong_password.value) == str(unknown_user.value)


def test_last_admin_cannot_be_demoted_or_deleted(store):
    admin = store.create(username="jose", password="senha-forte-1", role="admin")

    with pytest.raises(ConflictError):
        store.set_role(admin.id, "viewer")
    with pytest.raises(ConflictError):
        store.delete(admin.id)


def test_admin_can_be_demoted_when_another_exists(store):
    first = store.create(username="jose", password="senha-forte-1", role="admin")
    store.create(username="ana", password="senha-forte-1", role="admin")

    assert store.set_role(first.id, "operator").role == "operator"


def test_change_password_requires_current_password(store):
    user = store.create(username="maria", password="senha-forte-1")

    with pytest.raises(AuthorizationError):
        store.change_password(user.id, current_password="errada-errada", new_password="nova-senha-2")

    store.change_password(user.id, current_password="senha-forte-1", new_password="nova-senha-2")
    assert store.authenticate(username="maria", password="nova-senha-2")
