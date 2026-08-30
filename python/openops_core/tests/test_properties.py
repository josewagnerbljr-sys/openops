"""
Testes baseados em propriedades (property-based testing) do core.

Em vez de exemplos fixos escritos à mão, o Hypothesis gera centenas de
entradas — incluindo casos extremos que ninguém pensaria em testar
manualmente (strings vazias, unicode exótico, listas enormes, números
no limite) — e verifica que invariantes do sistema valem para todas
elas. Quando uma falha é encontrada, o Hypothesis automaticamente
"encolhe" (shrink) o caso até o exemplo mínimo que ainda reproduz o bug.
"""

from __future__ import annotations

from hypothesis import given, strategies as st

from openops_core.errors import (
    OpenOpsError,
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthorizationError,
    ConfigurationError,
    IntegrationError,
    MaintenanceError,
    http_status_for,
)
from openops_core.registry import ModuleRegistry, ModuleInfo, VALID_CATEGORIES
from openops_core.db import Database, Migration

ALL_ERROR_TYPES = [
    OpenOpsError,
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthorizationError,
    ConfigurationError,
    IntegrationError,
    MaintenanceError,
]

KNOWN_HTTP_STATUSES = {403, 404, 409, 422, 500, 502}


@given(
    message=st.text(min_size=1, max_size=200),
    error_type=st.sampled_from(ALL_ERROR_TYPES),
)
def test_http_status_for_always_returns_a_known_status(message, error_type):
    """Para QUALQUER mensagem e QUALQUER tipo de erro do OpenOps, o
    código HTTP resolvido é sempre um dos valores conhecidos e
    documentados — nunca None, nunca um valor fora do conjunto mapeado.
    """
    error = error_type(message)

    status = http_status_for(error)

    assert status in KNOWN_HTTP_STATUSES


@given(message=st.text(min_size=1, max_size=200))
def test_to_dict_always_roundtrips_the_message(message):
    """Para QUALQUER mensagem (incluindo unicode, emojis, strings com
    aspas ou caracteres de controle), to_dict() sempre preserva a
    mensagem original exatamente.
    """
    error = ValidationError(message)

    assert error.to_dict()["message"] == message


@given(
    names=st.lists(
        st.text(alphabet=st.characters(whitelist_categories=["L", "N"]), min_size=1, max_size=20),
        min_size=0,
        max_size=15,
        unique=True,
    )
)
def test_registry_list_always_matches_registered_names(names):
    """Para QUALQUER conjunto de nomes únicos registrados, list()
    devolve exatamente esses nomes — nem a mais, nem a menos — e sempre
    em ordem alfabética, não importa em que ordem foram registrados.
    """
    registry = ModuleRegistry()
    for name in names:
        registry.register(ModuleInfo(name=name, version="0.1.0"))

    listed_names = [m.name for m in registry.list()]

    assert listed_names == sorted(names)
    assert len(registry) == len(names)


@given(category=st.sampled_from(sorted(VALID_CATEGORIES)))
def test_any_valid_category_is_accepted(category):
    """Toda categoria declarada como válida em VALID_CATEGORIES de fato
    é aceita pelo construtor de ModuleInfo, sem exceção — evita que a
    lista de categorias "documentada" divirja silenciosamente da que é
    realmente aplicada.
    """
    info = ModuleInfo(name="x", version="0.1.0", category=category)

    assert info.category == category


@given(
    versions=st.lists(
        st.integers(min_value=1, max_value=1000), min_size=1, max_size=20, unique=True
    )
)
def test_migrate_is_idempotent_regardless_of_call_count(versions):
    """Para QUALQUER conjunto de migrations com versões únicas, aplicar
    duas vezes seguidas produz o mesmo conjunto de versões aplicadas que
    aplicar uma vez só — migrar nunca duplica trabalho nem corrompe o
    histórico, não importa quantas vezes for chamado.
    """
    db = Database(":memory:")
    migrations = [
        Migration(version=v, name=f"migration_{v}", sql=f"CREATE TABLE t_{v} (id INTEGER);")
        for v in versions
    ]

    db.migrate(migrations)
    applied_once = db.applied_versions()

    db.migrate(migrations)  # chamar de novo não deve fazer nada novo
    applied_twice = db.applied_versions()

    assert applied_once == applied_twice == set(versions)
