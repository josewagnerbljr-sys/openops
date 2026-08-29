# openops-cli (Go)

CLI do OpenOps, compilada como binário único — sem dependências externas — para cumprir o requisito de "instalação reproduzível do zero" descrito no [ARCHITECTURE.md](../../ARCHITECTURE.md).

## Build

```bash
go build -o openops-cli .
```

## Comandos disponíveis

```bash
./openops-cli version
./openops-cli health --path /caminho/do/repositorio
```

O comando `health` é a primeira fatia real do **Structural Health Engine**: hoje verifica a presença de arquivos e pastas essenciais (`README.md`, `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`, `.github/workflows`) e calcula um score de saúde. Cresce nas próximas fases para cobrir imports, dependências, AST, migrations e mais — veja o [ROADMAP.md](../../ROADMAP.md).

O comando `docgen` gera um relatório HTML autocontido (sem CDN, sem dependência de internet) a partir de qualquer diretório de código, com detecção de linguagem (Python, Go, Rust, JavaScript/TypeScript, JSON) e realce de sintaxe real via regex — não é decoração estática, cada token é classificado (comentário, string, número, palavra-chave):

```bash
./openops-cli docgen --path /caminho/do/projeto --out relatorio.html --title "Meu Projeto"
```

Arquivos maiores que 300 KB, conteúdo binário e pastas como `.git`, `node_modules`, `target`, `__pycache__` são ignorados automaticamente.

## Rodar os testes

```bash
go vet ./...
go test ./... -v
```
