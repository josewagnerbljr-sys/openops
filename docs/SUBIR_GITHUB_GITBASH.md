# Subir o OpenOps para o GitHub — passo a passo no Git Bash

Projeto no seu computador: `D:\openops-mvp`  →  no Git Bash o caminho é **`/d/openops-mvp`**
Repositório: https://github.com/josewagnerbljr-sys/openops

> Cada bloco abaixo é copiar-e-colar. Leia a saída de cada comando antes de passar para o próximo.

---

## 0. Conferir as ferramentas

```bash
git --version
python --version        # precisa ser 3.10 ou mais novo. Se der erro, use:  py --version
```

## 1. Entrar na pasta e descobrir em que situação ela está

```bash
cd /d/openops-mvp
ls -a
```

- Se aparecer **`.git`** na lista → siga o **Passo 2A**.
- Se **não** aparecer `.git` → siga o **Passo 2B**.

### 2A. A pasta já é um repositório Git

```bash
git remote -v                       # deve mostrar origin = https://github.com/josewagnerbljr-sys/openops.git
git branch --show-current           # anote o nome (main?)
git fetch origin
git status
```

Se `git remote -v` vier **vazio**:

```bash
git remote add origin https://github.com/josewagnerbljr-sys/openops.git
git fetch origin
```

Se o `git status` disser que a sua `main` está **atrás** do `origin/main` (behind), traga as novidades antes:

```bash
git pull --rebase origin main
```

### 2B. A pasta NÃO é um repositório ainda

```bash
git init -b main
git remote add origin https://github.com/josewagnerbljr-sys/openops.git
git fetch origin
git reset origin/main               # alinha o histórico SEM mexer nos seus arquivos
git status                          # agora aparece só o que é novo/diferente
```

## 3. Confirmar quem assina os commits (uma vez só)

```bash
git config user.name
git config user.email
```

Se algum vier vazio:

```bash
git config user.name  "José Wagner Blanco Júnior"
git config user.email "josewagnerbljr.sys@gmail.com"
```

## 4. Testar antes de subir (2 minutos)

```bash
pip install pytest hypothesis
python -m pytest test_project.py -q
cd python && python -m pytest -q openops_web/tests openops_core/tests openops_business/tests
cd ..
```

- Os testes da **API FastAPI** só rodam depois de `pip install -r requirements-api.txt`. Se não instalar, o GitHub (CI) roda por você.
- Se algum teste falhar, **pare aqui** e me mande a mensagem.

Teste o sistema de verdade, no navegador:

```bash
read -s -p "Senha do admin (min. 8 caracteres): " OPENOPS_ADMIN_PASSWORD; echo
export OPENOPS_ADMIN_PASSWORD
python openops.py --db /tmp/teste-openops.db init --admin jose --demo
unset OPENOPS_ADMIN_PASSWORD
python openops.py --db /tmp/teste-openops.db serve --open       # Ctrl+C para parar
```

## 5. Criar o ramo da entrega

```bash
git checkout -b cs50-final
```

## 6. Ver o que vai subir (e barrar lixo)

```bash
git status --short
git add -A
git diff --cached --stat | tail -5

# Não pode aparecer nada abaixo: banco, log, chave, .env, cache, binários.
git diff --cached --name-only | grep -E '\.(db|log|secret|env|pem|key)$|openops\.config\.json|__pycache__|/target/|node_modules' || echo "OK: nada indevido"
```

Se listar algum arquivo indevido, tire-o do envio (troque `ARQUIVO`):

```bash
git restore --staged ARQUIVO
```

Os avisos `LF will be replaced by CRLF` são normais no Windows e **não** são erro.

## 7. Criar o commit

```bash
git commit \
  -m "feat: micro-site HTML, CLI openops.py, testes e README do projeto final CS50" \
  -m "Troca o uso por API por um micro-site operável sem programar (estoque, produtos, clientes, usuários), corrige escalonamento de privilégio no cadastro, concorrência no estoque e remoção de produto com histórico, e adiciona README no formato CS50." \
  -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

> A última linha registra no histórico, de forma pública, o uso de IA — coerente com o README e com a regra do CS50. Se não quiser, apague essa linha `-m`.

## 8. Enviar para o GitHub

```bash
git push -u origin cs50-final
```

- Na primeira vez o Windows abre o navegador para você entrar no GitHub (Git Credential Manager). Autorize.
- Se pedir usuário/senha no terminal: o usuário é `josewagnerbljr-sys` e a "senha" é um **token** (GitHub → Settings → Developer settings → Personal access tokens, permissão `repo`). A senha normal da conta não funciona.

## 9. Conferir o CI e juntar na `main`

1. Abra: https://github.com/josewagnerbljr-sys/openops/pull/new/cs50-final
2. Título sugerido: `Projeto final CS50: micro-site OpenOps` → **Create pull request**.
3. Aguarde as verificações (Actions): Python, **Micro-site**, Go e Rust devem ficar **verdes**.
   - Se algo ficar vermelho, **não faça o merge**: abra o job, copie o erro e me envie.
4. Verde → **Merge pull request** → **Confirm merge**.

Depois, no Git Bash, traga a `main` atualizada:

```bash
git checkout main
git pull origin main
git log --oneline -3
```

*(Alternativa sem Pull Request, só se você preferir e a `main` não for protegida:)*

```bash
git checkout main
git merge --no-ff cs50-final -m "Merge: projeto final CS50"
git push origin main
```

## 10. Marcar a versão da entrega (opcional, recomendado)

```bash
git tag -a cs50-submission-2026 -m "Versão enviada ao CS50 2026"
git push origin cs50-submission-2026
```

(A tag não começa com `v`, então não dispara o workflow de release assinado.)

## 11. Prova final: baixar do GitHub numa pasta limpa e rodar

```bash
cd /d
git clone https://github.com/josewagnerbljr-sys/openops.git openops-teste
cd openops-teste
read -s -p "Senha do admin: " OPENOPS_ADMIN_PASSWORD; echo; export OPENOPS_ADMIN_PASSWORD
python openops.py init --admin jose --demo
unset OPENOPS_ADMIN_PASSWORD
python openops.py serve --open
```

Se abrir o micro-site com os dados de exemplo, o que está no GitHub é exatamente o que será avaliado.

## 12. Próximos passos do CS50 (depois do GitHub)

1. Gravar o vídeo → `docs/VIDEO_ROTEIRO.md` (≤ 3 min, YouTube **não listado**).
2. Colocar a URL no `README.md` (linha `#### Video Demo:`) e subir:

```bash
cd /d/openops-mvp
git checkout main && git pull origin main
# edite o README.md (VS Code, Bloco de Notas...), depois:
git add README.md
git commit -m "docs: adiciona URL do vídeo de demonstração"
git push origin main
```

3. Enviar com o submit50 (veja `docs/SUBMISSAO_CS50.md`, passos 5 e 6):

```bash
pip install submit50
cd /d/openops-mvp
du -sh --exclude=.git .             # precisa ser menor que 100 MB
submit50 cs50/problems/2026/x/project
```

4. Abrir https://cs50.me/cs50x e reivindicar o certificado **antes de 31/12/2026 23:59 UTC**.

---

## Se der erro

| Mensagem | Causa e solução |
|---|---|
| `python: command not found` | Use `py` no lugar de `python`, ou instale o Python 3.10+ (marque "Add to PATH") |
| `! [rejected] ... (fetch first)` ou `non-fast-forward` | Alguém (ou você, pelo site) mudou o GitHub. Rode `git pull --rebase origin cs50-final` e repita o `git push` |
| `Permission denied` / `403` / `Authentication failed` | Faça login de novo (Passo 8) ou use um token |
| `fatal: not a git repository` | Você não está na pasta certa. `cd /d/openops-mvp` e veja o Passo 1 |
| `nothing to commit` | Os arquivos novos não estão em `/d/openops-mvp`. Copie-os para lá e repita o Passo 6 |
| `error: Your local changes ... would be overwritten` ao fazer pull | Faça o commit antes (Passos 6 e 7) e só então `git pull --rebase` |
| `UnicodeEncodeError` ao rodar `python openops.py ...` | Já corrigido nesta versão (`openops.py` força UTF-8). Se aparecer, confirme que está com o `openops.py` novo |
