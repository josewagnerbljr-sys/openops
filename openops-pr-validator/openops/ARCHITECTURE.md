# Arquitetura do OpenOps

## Visão e propósito

O OpenOps funde três ideias: OpenBusiness OS, OpenSOP e OpenOps. O resultado é uma base operacional reutilizável para pequenas e médias organizações, com módulos empresariais, processos, workflows, indicadores, segurança e engenharia de software integrada.

O projeto também tem finalidade educacional prática: pessoas de diferentes níveis de programação podem estudar o código, resolver issues, criar testes, documentar, desenvolver módulos e evoluir progressivamente para tarefas de maior complexidade — veja [CONTRIBUTING.md](CONTRIBUTING.md).

## Princípios

- Open source, transparente e colaborativo.
- Modularidade e baixo acoplamento.
- Security by design e privacy by design.
- Fork-friendly: instalação, testes e operação sem dependência secreta.
- Documentação como parte do produto.
- Learning by building: contribuições adequadas a iniciantes, intermediários e avançados.
- Observabilidade, diagnóstico e recuperação como capacidades de primeira classe.
- Automação graduada por risco; mudanças críticas exigem controles apropriados.
- Honestidade técnica: nenhum sistema é declarado absolutamente inviolável ou infalível.

## Stack poliglota e por quê

| Camada | Linguagem | Motivo |
|---|---|---|
| Business OS, API, OpenSOP, Plugins | **Python** | Produtividade de desenvolvimento, ecossistema maduro (FastAPI), facilidade de contribuição para iniciantes |
| CLI, Structural Health Engine, Event Bus de alta concorrência | **Go** | Binário único sem dependências para instalação reproduzível; concorrência nativa eficiente |
| Security (criptografia, gestão de chaves) | **Rust** | Segurança de memória garantida em tempo de compilação — propriedade crítica para código de criptografia |

## Arquitetura funcional

| Camada | Responsabilidade |
|---|---|
| Business OS | Cadastros, produtos, clientes, fornecedores, estoque, compras, vendas, custos, finanças e indicadores. |
| OpenSOP | Procedimentos, POPs, versões, responsáveis, checklists, evidências e auditoria. |
| Operations | Tarefas, workflows, eventos, metas, responsabilidades e execução. |
| Security | Criptografia, segredos, autenticação, autorização, auditoria e integridade. |
| Maintenance | Diagnóstico, testes, dependências, performance, snapshots e recuperação. |
| Structural Health | Leitura da estrutura, consistência, saúde dos módulos e geração de relatórios. |
| API/CLI/UI | Interfaces humanas, automação e integração. |
| Plugins/Integrations | Extensões setoriais e conectores externos. |

## Estrutura do repositório

```
openops/
├── python/openops_core/     # Business OS, API, plugins (Fase 1+)
├── go/openops-cli/          # CLI, Structural Health Engine
├── rust/openops-security/   # Camada Security (AEAD, chaves)
├── docs/
├── .github/workflows/       # CI
├── README.md
├── ARCHITECTURE.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── SECURITY.md
└── CODE_OF_CONDUCT.md
```

## Módulos do Business OS (planejados)

- **Business**: clientes, fornecedores, produtos, serviços, categorias, unidades e documentos.
- **Inventory**: entradas, saídas, inventário, lotes, validade, perdas, ajustes e rastreabilidade.
- **Purchasing**: fornecedores, cotações, pedidos e recebimentos.
- **Sales**: pedidos, itens, clientes e estados de venda.
- **Finance**: receitas, despesas, contas, fluxo de caixa e DRE simplificada.
- **Pricing**: custo, margem, markup e formação de preço.
- **Analytics**: KPIs, metas, tendências, alertas e relatórios.

## OpenSOP

Cada procedimento tem identidade, objetivo, escopo, pré-requisitos, responsáveis, materiais, etapas, pontos de controle, riscos, evidências, indicadores e histórico de versões.

Exemplo: `SOP-RESTAURANT-001` — abertura da cozinha → equipamentos → temperaturas → estoque → validade → mise en place → ocorrências → liberação.

## Verticais iniciais

| Vertical | Primeiro escopo |
|---|---|
| Restaurant/Pizzeria | Fichas técnicas, CMV, perdas, produção, estoque, compras e POPs. |
| Retail | Produtos, estoque, compras, vendas, margem e inventário. |
| Services | Clientes, contratos, tarefas, custos e execução. |
| Hospitality | Módulos operacionais específicos em fase posterior. |
| Manufacturing | Somente após validação da arquitetura comum. |

## Security

A camada de segurança (`rust/openops-security`) é um subsistema público, documentado e testável. AES-256-GCM é usado como cifra autenticada (AEAD), com nonce único por operação, gestão de chaves isolada e controles de acesso — sem tratar a cifra isolada como sinônimo de segurança.

| Camada | Objetivo | Controles |
|---|---|---|
| 1 — Data | Proteger dados sensíveis | AES-256-GCM (AEAD), nonce/IV correto, integridade |
| 2 — Storage/Secrets | Proteger chaves e segredos | Hierarquia de chaves, rotação, isolamento, permissões mínimas |
| 3 — Access/Runtime | Controlar execução e acesso | Autenticação, RBAC quando adequado, sessões, rate limiting, auditoria |

## Integridade e proteção contra adulteração

"Imutável" significa que alterações silenciosas não são aceitas pelo fluxo normal: uma mudança gera nova versão, novo hash e registro correspondente. Isso se aplica a manifests de release, hashes de integridade, migrações versionadas, logs de auditoria protegidos e snapshots antes de operações críticas.

Nenhum software local pode ser prometido como absolutamente inviolável contra alguém com controle total do ambiente. O objetivo é tornar adulteração detectável, alterações críticas rastreáveis e recuperação confiável.

## Self-Maintenance Engine (planejado)

| Etapa | Função |
|---|---|
| Detect | Encontrar sinais de erro ou degradação |
| Analyze | Correlacionar evidências e causas prováveis |
| Classify | Determinar severidade, confiança e impacto |
| Plan | Gerar plano de correção |
| Snapshot | Criar ponto de recuperação |
| Repair | Executar correções autorizadas |
| Validate | Executar testes pós-correção |
| Report | Registrar resultado e eventual rollback |

## Structural Health Engine

A primeira fatia deste motor já existe em `go/openops-cli` (comando `health`) e evolui incrementalmente. Escopo completo planejado:

- Estrutura de arquivos e diretórios
- Imports e referências inválidas
- Dependências e ciclos
- AST e consistência sintática
- Configurações e schemas
- Banco de dados e migrations
- Estado dos testes
- Integridade de arquivos críticos
- Performance e regressões
- Dependências vulneráveis (scanners confiáveis)
- Saúde por módulo e score global

Exemplo de saída: `ARCHITECTURE PASS | DATABASE PASS | SECURITY WARNING | TESTS PASS | CRITICAL 0 | WARNINGS 2 | HEALTH 92%`

## Preparação para forks

- Instalação reproduzível do zero
- Banco e migrations reproduzíveis
- Configuração por ambiente
- CLI administrativa (binário único, sem dependências)
- Testes executáveis localmente
- Documentação arquitetural
- Schemas e contratos públicos
- Funcionamento básico sem segredos privados

## Relação com componentes proprietários

Um eventual motor de núcleo proprietário e um validador automático proprietário, quando utilizados, permanecem fora deste repositório público e não são necessários para o funcionamento básico do OpenOps. A separação é arquitetural: interfaces públicas, implementação privada. O OpenOps não contém código ofuscado, backdoors, dependências secretas ou bloqueios artificiais contra forks.

## Governança colaborativa

| Nível | Contribuições | Evolução |
|---|---|---|
| L0 — Usuário | Issues, reprodução de bugs, documentação | GitHub, comunicação e diagnóstico |
| L1 — Iniciante | Docs, exemplos, testes simples e pequenos fixes | Git, testes e revisão |
| L2 — Intermediário | Módulos, APIs e refatorações | Arquitetura e integração |
| L3 — Avançado | Segurança, performance e core modules públicos | Engenharia de sistemas |
| L4 — Maintainer | Revisão, releases e arquitetura | Governança e estabilidade |

## Critério de sucesso

O OpenOps será considerado maduro quando uma pessoa que não participou da sua criação conseguir clonar o repositório, instalar o sistema, executar os testes, utilizar os módulos básicos, compreender a arquitetura, criar uma extensão, diagnosticar um problema e enviar uma contribuição revisável pela comunidade.
