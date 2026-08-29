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

O comando `secscan` varre o mesmo diretório em busca de segredos vazados (chaves de API, tokens, chaves privadas PEM) usando padrões de alta confiança — a mesma ferramenta usada pela validação automática de PRs (veja [SECURITY.md](../../SECURITY.md)):

```bash
./openops-cli secscan --path /caminho/do/projeto
```

Se uma linha contiver um valor que *parece* segredo mas não é (ex.: uma chave de exemplo em documentação ou em teste), adicione `secscan:ignore` em um comentário na mesma linha para excluí-la da varredura, deliberadamente e de forma visível no código.

## Rodar os testes

```bash
go vet ./...
go test ./... -v
```
