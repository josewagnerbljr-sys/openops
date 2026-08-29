# Roadmap do OpenOps

## Status atual

- ✅ **Fase 0 — Fundação**: repositório, licença (Apache 2.0), documentação de arquitetura, CI, política de segurança, código de conduta.
- ✅ **Fase 1 — Core técnico (fatia inicial)**: config, logging estruturado e event bus funcionando em Python (`openops_core`), com testes automatizados. CLI inicial e Structural Health Engine mínimo funcionando em Go (`openops-cli`). Camada Security inicial funcionando em Rust (`openops-security`), com criptografia autenticada AES-256-GCM testada.
- ⬜ Restante da Fase 1 em diante: ver cronograma completo abaixo.

## Cronograma mestre

| Fase | Entrega |
|---|---|
| 0 — Fundação | Repositório, licença, manifesto, arquitetura, CODEOWNERS, templates, CI e política de segurança. |
| 1 — Core técnico | Configuração, logging, eventos, registry, erros, contratos e banco base. |
| 2 — Business | Cadastros, produtos, clientes, fornecedores, estoque, compras e vendas. |
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
| P0 | Definir contratos públicos, banco inicial e estrutura modular. |
| P1 | Business OS. |
| P1 | OpenSOP. |
| P1 | Operations/Workflow. |
| P1 | Security *(fatia inicial concluída — expandir para camadas 2 e 3)*. |
| P1 | Maintenance/Health *(fatia inicial concluída em Go — expandir escopo de checks)*. |
| P2 | API/CLI e UI inicial. |
| P2 | Plugin SDK e primeiro vertical Restaurant/Pizzeria. |
| P3 | Hardening, auditoria externa, benchmarks e release 1.0. |

## Definition of Done (aplicada a cada item do roadmap)

Ver a lista completa em [CONTRIBUTING.md](CONTRIBUTING.md#definition-of-done).
