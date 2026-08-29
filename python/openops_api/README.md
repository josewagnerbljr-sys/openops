# openops-api (Python)

API REST do OpenOps, em FastAPI — uma fatia adiantada da Fase 9 do [ROADMAP](../../ROADMAP.md), construída junto com o primeiro módulo de Business OS para já ter algo demonstrável de ponta a ponta.

## Rodar localmente

```bash
cd python
pip install -e ".[dev]"
python -m uvicorn openops_api.main:app --reload
```

Depois acesse:
- `http://127.0.0.1:8000/` — lista os módulos registrados
- `http://127.0.0.1:8000/docs` — documentação interativa (Swagger UI), gerada automaticamente pelo FastAPI
- `http://127.0.0.1:8000/products` — CRUD de produtos

## Tratamento de erros

Toda exceção de `openops_core.errors.OpenOpsError` (e subclasses) é convertida automaticamente numa resposta HTTP com o código certo — `ValidationError` vira 422, `NotFoundError` vira 404, `ConflictError` vira 409, e assim por diante (veja `http_status_for` em `openops_core/errors.py`). O corpo da resposta segue sempre o mesmo formato:

```json
{
  "error": "validation_error",
  "message": "dados de produto inválidos",
  "details": {"price": "deve ser maior que zero"}
}
```

## Rodar os testes

```bash
python -m pytest openops_api/tests -v
```

Os testes usam `create_app()` com banco `:memory:` e um `ModuleRegistry` isolado por teste — nenhum estado é compartilhado entre eles, mesmo rodando em paralelo.

## Testar manualmente com curl

```bash
curl -X POST http://127.0.0.1:8000/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Pão de Queijo", "price": 3.5, "stock": 100, "category": "salgados"}'

curl http://127.0.0.1:8000/products
```
