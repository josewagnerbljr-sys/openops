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

config = load_config()  # defaults -> arquivo (opcional) -> variáveis OPENOPS_*
logger = get_logger("meu_modulo")
logger.info("iniciando", category=LogCategory.CORE)

bus = EventBus()
bus.subscribe("sop.completed", lambda event: print(event.payload))
bus.publish("sop.completed", {"sop_id": "SOP-RESTAURANT-001"})
```

## Módulos

| Módulo | Responsabilidade |
|---|---|
| `config.py` | Configuração em camadas (defaults → arquivo JSON → env `OPENOPS_*`) |
| `logging.py` | Logging estruturado em JSON, com `LogCategory` por camada funcional |
| `events.py` | Event bus síncrono, thread-safe, em processo |
