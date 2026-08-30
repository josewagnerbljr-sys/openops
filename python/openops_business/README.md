# openops-business (Python)

Módulos de negócio do OpenOps — a implementação concreta da camada "Business OS" descrita em [ARCHITECTURE.md](../../ARCHITECTURE.md). Cada módulo segue o mesmo padrão: `models.py` (domínio + validação) → `repository.py` (persistência) → `service.py` (fachada de negócio + registro no `ModuleRegistry`) → `router.py` (rotas REST, consumidas por `openops_api`).

## Módulos implementados

| Módulo | Status | O que cobre |
|---|---|---|
| `products/` | ✅ Completo | Cadastro de produtos: nome, preço, estoque, categoria — CRUD completo |
| `customers/` | ✅ Completo | Cadastro de clientes: nome, e-mail (único, validado), telefone, documento — CRUD completo com busca por nome |
| `inventory/` | ✅ Completo | Movimentação de estoque (entrada/saída/ajuste), integrado ao módulo de Produtos, publica eventos `stock.changed`/`stock.low` via EventBus |
| `suppliers/` | ⬜ Planejado | Fornecedores |
| `sales/` | ⬜ Planejado | Pedidos de venda |

## Rodar os testes

```bash
cd python
python -m pytest openops_business/tests -v
```

## Exemplo — módulo de Produtos

```python
from openops_core.db import Database
from openops_business.products import ProductService

db = Database("openops.db")
service = ProductService(db)  # aplica as migrations do módulo automaticamente

product = service.create_product(name="Café Especial", price=24.90, stock=10, category="bebidas")
service.list_products(category="bebidas")
```

Para expor via HTTP, veja [`openops_api`](../openops_api/README.md).
