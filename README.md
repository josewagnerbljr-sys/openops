<div align="center">

# OpenOps

**Open Source Business Operations Platform**

Gestão empresarial, processos (OpenSOP), execução operacional, segurança, manutenção e saúde estrutural — em uma base modular, aberta e fork-friendly.

[![CI](https://github.com/josewagnerbljr-sys/openops/actions/workflows/ci.yml/badge.svg)](https://github.com/josewagnerbljr-sys/openops/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](python/)
[![Go](https://img.shields.io/badge/Go-1.22+-00ADD8?logo=go&logoColor=white)](go/openops-cli/)
[![Rust](https://img.shields.io/badge/Rust-2021-000000?logo=rust&logoColor=white)](rust/openops-security/)

</div>

---

## O que é o OpenOps

O OpenOps funde três ideias — **OpenBusiness OS**, **OpenSOP** e **OpenOps** — em uma base operacional reutilizável para pequenas e médias organizações: cadastros, estoque, compras, vendas, procedimentos operacionais padrão (POPs), workflows, indicadores, segurança e engenharia de software integrada.

O projeto tem também finalidade **educacional**: pessoas de diferentes níveis de programação podem estudar o código, resolver issues, escrever testes, documentar e evoluir progressivamente — veja a tabela de governança em [CONTRIBUTING.md](CONTRIBUTING.md).

> "Build it. Understand it. Improve it. Share it."

## Por que três linguagens

Este é um monorepo intencionalmente poliglota — cada camada usa a linguagem mais adequada ao seu problema, não a mesma linguagem por padrão:

| Linguagem | Onde | Por quê |
|---|---|---|
| 🐍 **Python** | `python/openops_core`, `python/openops_business`, `python/openops_api` | Core, Business OS, API e plugins — produtividade e ecossistema |
| 🐹 **Go** | `go/openops-cli` | CLI e Structural Health Engine — binário único, sem dependências, instalação reproduzível |
| 🦀 **Rust** | `rust/openops-security` | Camada Security — segurança de memória garantida em compilação, ideal para criptografia |

Detalhes completos em [ARCHITECTURE.md](ARCHITECTURE.md).

## Bônus: gerador de documentação com realce de sintaxe

O `openops-cli` também inclui o comando `docgen`: aponte para qualquer diretório de código (não precisa ser o próprio OpenOps) e ele gera um relatório HTML autocontido — sem CDN, sem internet — com detecção automática de linguagem (Python, Go, Rust, JavaScript/TypeScript, JSON) e realce de sintaxe real, útil para demonstrações, portfólio e documentação rápida.

```bash
openops-cli docgen --path ./meu-projeto --out relatorio.html --title "Meu Projeto"
```

Veja um exemplo gerado a partir do próprio código do CLI em [`docs/examples/demo-report.html`](docs/examples/demo-report.html).

## Status do projeto

🚧 **Fase 2 do roadmap** — Fundação e Core técnico completos; três módulos de negócio (Produtos, Clientes, Estoque) funcionando de ponta a ponta e integrados entre si via EventBus, com API REST real. 149 testes Python + 10 Rust + Go, todos passando em CI. Veja o [ROADMAP.md](ROADMAP.md) completo para as próximas fases.

## Quick start

```bash
git clone https://github.com/josewagnerbljr-sys/openops.git
cd openops
```

**Python — core (config, logging, events, errors, registry, db) + Business OS + API**
```bash
cd python
pip install -e ".[dev]"
python -m pytest -v

# Subir a API REST de verdade
python -m uvicorn openops_api.main:app --reload
# depois acesse http://127.0.0.1:8000/docs para a documentação interativa
```

**Go — CLI e Structural Health Engine**
```bash
cd go/openops-cli
go build -o openops-cli .
./openops-cli health --path ../..
./openops-cli docgen --path ../.. --out relatorio.html --title "Meu Projeto"
./openops-cli secscan --path ../..
```

**Rust — camada Security (AES-256-GCM)**
```bash
cd rust/openops-security
cargo test
```

## Estrutura do repositório

```
openops/
├── python/openops_core/     # Core: config, logging, events, errors, registry, db
├── python/openops_business/ # Módulos de negócio (Produtos, e os que vierem depois)
├── python/openops_api/      # API REST (FastAPI)
├── go/openops-cli/          # CLI, Structural Health Engine, docgen, secscan
├── rust/openops-security/   # Criptografia autenticada (AEAD)
├── docs/
├── .github/workflows/       # CI + validação automática de PR
├── ARCHITECTURE.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── SECURITY.md
└── CODE_OF_CONDUCT.md
```

## Releases assinadas

Toda tag `v*` publicada dispara build cross-plataforma (Linux/macOS/Windows, amd64/arm64) e assinatura keyless via [Sigstore/cosign](https://www.sigstore.dev/) — sem chave privada pra gerenciar, com verificação pública no [Rekor](https://rekor.sigstore.dev/). Veja as instruções de verificação nas notas de cada [release](https://github.com/josewagnerbljr-sys/openops/releases).

## Documentação

- [ARCHITECTURE.md](ARCHITECTURE.md) — visão, princípios, camadas e módulos planejados
- [ROADMAP.md](ROADMAP.md) — cronograma completo das 15 fases e marcos de maturidade
- [CONTRIBUTING.md](CONTRIBUTING.md) — como contribuir, por nível de experiência
- [SECURITY.md](SECURITY.md) — como reportar vulnerabilidades
- [THREAT_MODEL.md](THREAT_MODEL.md) — análise formal de ameaças (STRIDE)
- [MUTATION_TESTING.md](python/MUTATION_TESTING.md) — resultado real de mutation testing sobre o código
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## Licença

[Apache License 2.0](LICENSE) — © 2026 José Wagner Blanco Júnior.

## Contato

📧 [consultoriablanco8@gmail.com](mailto:consultoriablanco8@gmail.com) · 💼 [LinkedIn](https://www.linkedin.com/in/blancoconsultoria) · 🌐 [chefblanco.com.br](https://chefblanco.com.br/)
