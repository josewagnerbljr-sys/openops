# openops-core (Python)

Núcleo em Python do OpenOps: configuração em camadas, logging estruturado (JSON Lines) e event bus em processo. É a base sobre a qual o Business OS, a API e os plugins serão construídos (Fase 2+ do [ROADMAP](../ROADMAP.md)).

## Instalar

```bash
pip install -e ".[dev]"
```

## Rodar os testes

```bash
python -m pytest -v
```

## Uso básico

```python
from openops_core import load_config, get_logger, LogCategory, EventBus
from openops_core import ValidationError, NotFoundError, http_status_for
from openops_core import ModuleRegistry, ModuleInfo, register_module
from openops_core import Database, Migration

config = load_config()  # defaults -> arquivo (opcional) -> variáveis OPENOPS_*
logger = get_logger("meu_modulo")
logger.info("iniciando", category=LogCategory.CORE)

bus = EventBus()
bus.subscribe("sop.completed", lambda event: print(event.payload))
bus.publish("sop.completed", {"sop_id": "SOP-RESTAURANT-001"})

# Erros de domínio, com mapeamento pronto para código HTTP (Fase 9)
try:
    raise NotFoundError("produto não encontrado", details={"id": 42})
except NotFoundError as exc:
    assert http_status_for(exc) == 404

# Registry de módulos
@register_module(name="pricing", version="0.1.0", category="business")
class PricingModule:
    ...

# Banco base com migrations versionadas
db = Database("openops.db")
db.migrate([
    Migration(1, "create_products", "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT);"),
])
db.execute("INSERT INTO products (name) VALUES (?)", ("Café",))
```

## Módulos

| Módulo | Responsabilidade |
|---|---|
| `config.py` | Configuração em camadas (defaults → arquivo JSON → env `OPENOPS_*`) |
| `logging.py` | Logging estruturado em JSON, com `LogCategory` por camada funcional |
| `events.py` | Event bus síncrono, thread-safe, em processo |
| `errors.py` | Hierarquia de exceções de domínio, com mapeamento para código HTTP |
| `registry.py` | Registry thread-safe de módulos/plugins, com decorator de registro |
| `db.py` | Conexão SQLite + executor de migrations versionadas |
