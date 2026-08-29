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
| 🐍 **Python** | `python/openops_core` | Business OS, API, OpenSOP e plugins — produtividade e ecossistema |
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

🚧 **Fase 0/1 do roadmap** — fundação pronta, núcleo funcional inicial nas três linguagens, com testes automatizados passando em CI. Veja o [ROADMAP.md](ROADMAP.md) completo para as próximas 14 fases.

## Quick start

```bash
git clone https://github.com/josewagnerbljr-sys/openops.git
cd openops
```

**Python — core (config, logging, events)**
```bash
cd python
pip install -e ".[dev]"
python -m pytest -v
```

**Go — CLI e Structural Health Engine**
```bash
cd go/openops-cli
go build -o openops-cli .
./openops-cli health --path ../..
./openops-cli docgen --path ../.. --out relatorio.html --title "Meu Projeto"
```

**Rust — camada Security (AES-256-GCM)**
```bash
cd rust/openops-security
cargo test
```

## Estrutura do repositório

```
openops/
├── python/openops_core/     # Business OS, API, plugins
├── go/openops-cli/          # CLI, Structural Health Engine
├── rust/openops-security/   # Criptografia autenticada (AEAD)
├── docs/
├── .github/workflows/ci.yml
├── ARCHITECTURE.md
├── ROADMAP.md
├── CONTRIBUTING.md
├── SECURITY.md
└── CODE_OF_CONDUCT.md
```

## Documentação

- [ARCHITECTURE.md](ARCHITECTURE.md) — visão, princípios, camadas e módulos planejados
- [ROADMAP.md](ROADMAP.md) — cronograma completo das 15 fases e marcos de maturidade
- [CONTRIBUTING.md](CONTRIBUTING.md) — como contribuir, por nível de experiência
- [SECURITY.md](SECURITY.md) — como reportar vulnerabilidades
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

## Licença

[Apache License 2.0](LICENSE) — © 2026 José Wagner Blanco Júnior.

## Contato

📧 [consultoriablanco8@gmail.com](mailto:consultoriablanco8@gmail.com) · 💼 [LinkedIn](https://www.linkedin.com/in/blancoconsultoria) · 🌐 [chefblanco.com.br](https://chefblanco.com.br/)
