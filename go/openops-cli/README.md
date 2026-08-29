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

## Rodar os testes

```bash
go vet ./...
go test ./... -v
```
