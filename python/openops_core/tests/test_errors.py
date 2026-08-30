import pytest

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


def test_base_error_has_code_and_to_dict():
    error = OpenOpsError("algo deu errado", details={"field": "nome"})

    assert error.code == "openops_error"
    assert error.to_dict() == {
        "error": "openops_error",
        "message": "algo deu errado",
        "details": {"field": "nome"},
    }


def test_str_of_error_contains_the_message():
    """A mensagem passada ao construtor deve chegar até str(exception) —
    não só ficar disponível via .message. Isso importa porque logs e
    tracebacks não capturados usam str(exception), não .message.
    """
    error = ValidationError("preço deve ser positivo")

    assert str(error) == "preço deve ser positivo"


def test_subclasses_have_distinct_codes():
    codes = {
        ValidationError("x").code,
        NotFoundError("x").code,
        ConflictError("x").code,
        AuthorizationError("x").code,
        ConfigurationError("x").code,
        IntegrationError("x").code,
        MaintenanceError("x").code,
    }

    assert len(codes) == 7  # nenhum código duplicado


def test_details_default_to_empty_dict():
    error = ValidationError("campo obrigatório")

    assert error.details == {}


@pytest.mark.parametrize(
    "error,expected_status",
    [
        (ValidationError("x"), 422),
        (NotFoundError("x"), 404),
        (ConflictError("x"), 409),
        (AuthorizationError("x"), 403),
        (ConfigurationError("x"), 500),
        (IntegrationError("x"), 502),
        (MaintenanceError("x"), 500),
        (OpenOpsError("x"), 500),
    ],
)
def test_http_status_for_known_errors(error, expected_status):
    assert http_status_for(error) == expected_status


def test_http_status_for_custom_subclass_falls_back_via_mro():
    class CustomNotFound(NotFoundError):
        pass

    assert http_status_for(CustomNotFound("x")) == 404


def test_errors_are_catchable_as_base_class():
    with pytest.raises(OpenOpsError):
        raise ValidationError("teste")
