# Roadmap do OpenOps

## Status atual

- ✅ **Fase 1 — Core técnico**: config, logging estruturado, event bus, hierarquia de erros, registry de módulos e camada de banco base (SQLite + migrations versionadas) — todos em Python (`openops_core`). CLI (`health`, `docgen`, `secscan`) funcionando em Go. Camada Security em Rust (AES-256-GCM), testada.
- ✅ **Fase 2 — Business OS (primeira fatia)**: módulo de **Produtos** completo — modelo de domínio validado, repositório com persistência SQLite, serviço de negócio registrado no registry, e API REST real em FastAPI (`openops_api`) com CRUD completo, testada de ponta a ponta (incluindo requisições HTTP reais). 75 testes Python no total.
- ✅ **Bônus (fora do cronograma original)**: comando `docgen` no `openops-cli` — gerador de relatório HTML com detecção automática de linguagem e realce de sintaxe, útil como ferramenta standalone para qualquer projeto, não só o OpenOps.
- ✅ **Bônus**: pipeline de validação automática de PR em duas camadas seguras (`ci.yml` + `pr-comment.yml`), com scanner de segredos (`secscan`) e rejeição automática apenas para credenciais de alta confiança — bloqueio de usuário permanece uma decisão manual do mantenedor (`block-contributor.yml`).
- ⬜ Restante da Fase 2 (Inventory, Purchasing, Sales, Finance, Pricing, Analytics) e fases seguintes: ver cronograma completo abaixo.

## Cronograma mestre

| Fase | Entrega |
|---|---|
| 0 — Fundação | Repositório, licença, manifesto, arquitetura, CODEOWNERS, templates, CI e política de segurança. *(concluído)* |
| 1 — Core técnico | Configuração, logging, eventos, registry, erros, contratos e banco base. *(concluído)* |
| 2 — Business | Cadastros, produtos, clientes, fornecedores, estoque, compras e vendas. *(Produtos concluído; Clientes/Fornecedores/Estoque/Compras/Vendas pendentes)* |
| 3 — Finance/Pricing | Custos, fluxo de caixa, DRE, margem e formação de preço. |
| 4 — OpenSOP | Procedimentos, versões, checklists, evidências e auditoria. |
| 5 — Operations | Tasks, workflows, eventos, responsáveis, metas e KPIs. |
| 6 — Security | AES-256 aplicado corretamente, secrets, access control e auditoria. |
| 7 — Maintenance | Diagnóstico, integridade, dependências, snapshots e recovery. |
| 8 — Health | Structural scan, health score, relatórios e histórico. |
| 9 — API/CLI | Interfaces estáveis e automação. |
| 10 — UI | Interface web inicial, acessibilidade e UX. |
| 11 — Plugins | SDK, contratos, exemplos e ecossistema. |
| 12 — Verticais | Restaurant/Pizzeria e demais extensões. |
| 13 — Hardening | Stress tests, benchmarks, security review e documentação. |
| 14 — Release 1.0 | Instalação independente, estabilidade e documentação completa. |

## Marcos de maturidade

| Marco | Critério |
|---|---|
| Prototype | Arquitetura e módulos experimentais. |
| Alpha | Fluxos principais e testes iniciais. |
| Beta | Instalação reproduzível, segurança base, APIs e health/maintenance. |
| RC | Hardening, regressão controlada e documentação completa. |
| 1.0 | Terceiros conseguem instalar, usar, modificar e manter o sistema sem depender do autor. |

## Backlog inicial (por prioridade)

| Prioridade | Item |
|---|---|
| P0 | Criar repositório, licença, manifesto, arquitetura, CI e política de segurança. *(concluído)* |
| P0 | Definir contratos públicos, banco inicial e estrutura modular. *(banco inicial e registry concluídos; contratos públicos — ex.: OpenAPI — ficam para a Fase 9)* |
| P1 | Business OS. *(Produtos concluído — API REST completa e testada)* |
| P1 | OpenSOP. |
| P1 | Operations/Workflow. |
| P1 | Security *(fatia inicial concluída — expandir para camadas 2 e 3)*. |
| P1 | Maintenance/Health *(fatia inicial concluída em Go — expandir escopo de checks)*. |
| P2 | API/CLI e UI inicial. |
| P2 | Plugin SDK e primeiro vertical Restaurant/Pizzeria. |
| P3 | Hardening, auditoria externa, benchmarks e release 1.0. |

## Definition of Done (aplicada a cada item do roadmap)

Ver a lista completa em [CONTRIBUTING.md](CONTRIBUTING.md#definition-of-done).
