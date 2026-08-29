# Contribuindo com o OpenOps

Obrigado pelo interesse! O OpenOps é, por design, um projeto que cresce com contribuidores de todos os níveis — veja a tabela de governança abaixo antes de escolher onde começar.

## Estrutura do repositório

Este é um monorepo poliglota:

| Pasta | Linguagem | Responsabilidade |
|---|---|---|
| `python/openops_core` | Python 3.10+ | Business OS, API, OpenSOP, plugins |
| `go/openops-cli` | Go 1.22+ | CLI, Structural Health Engine, distribuição em binário único |
| `rust/openops-security` | Rust (edition 2021) | Criptografia autenticada (AEAD), gestão de chaves |

Cada subprojeto tem seu próprio `README.md` com instruções específicas de build e teste.

## Como rodar tudo localmente

```bash
# Python
cd python && pip install -e ".[dev]" && python -m pytest

# Go
cd go/openops-cli && go build ./... && go test ./...

# Rust
cd rust/openops-security && cargo build && cargo test
```

## Governança e níveis de contribuição

| Nível | Tipo de contribuição |
|---|---|
| **L0 — Usuário** | Issues, reprodução de bugs, documentação |
| **L1 — Iniciante** | Docs, exemplos, testes simples, pequenos fixes |
| **L2 — Intermediário** | Módulos, APIs, refatorações |
| **L3 — Avançado** | Segurança, performance, core modules públicos |
| **L4 — Maintainer** | Revisão, releases, arquitetura |

Não é necessário "pedir permissão" para contribuir no seu nível — abra um PR e a revisão orienta o resto.

## Definition of Done

Antes de abrir um PR, confirme:

- [ ] Código implementado e revisado por você mesmo primeiro
- [ ] Testes relevantes adicionados (e passando localmente)
- [ ] Documentação atualizada, se aplicável
- [ ] Nenhum secret ou credencial no commit
- [ ] Mudanças que quebram compatibilidade estão documentadas no PR
- [ ] CI passando

## Convenção de commits

Seguimos o padrão do tipo `tipo: descrição curta`, por exemplo:

```
feat: adicionar endpoint de listagem de SOPs
fix: corrigir race condition no event bus
docs: atualizar guia de instalação
test: adicionar cobertura para módulo de config
```

## Reportando vulnerabilidades

Não abra uma issue pública para falhas de segurança — veja [SECURITY.md](SECURITY.md).
