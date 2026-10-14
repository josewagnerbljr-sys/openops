# Submissão do projeto final CS50 2026 — passo a passo (Git Bash)

Prazo: **31/12/2026 às 23:59 UTC** (isso é 20:59 em Brasília). Os três passos abaixo precisam estar concluídos: **vídeo**, **README + submit50** e **gradebook (cs50.me/cs50x)**.

> Regras oficiais conferidas em https://cs50.harvard.edu/x/project/ — se algo divergir, vale a página oficial.

---

## Antes de tudo: o que só você pode fazer

| Item | Por que é seu |
|---|---|
| Ler e entender o código | A regra do CS50 é que a **essência do trabalho seja sua**; IA só amplifica. Você precisa conseguir explicar cada arquivo. Use a seção 3 do README como roteiro de estudo. |
| Gravar o vídeo (≤ 3 min) | Precisa mostrar seu nome, usuários GitHub/edX, cidade/país e data. Veja `docs/VIDEO_ROTEIRO.md`. |
| Colar a URL do vídeo no README | Está como `<PASTE YOUR YOUTUBE URL HERE>`. |
| Conferir a seção "Use of AI assistance" do README | Ela precisa refletir a **verdade** sobre o que você fez e o que a IA fez. Ajuste com suas palavras. |

---

## Passo 1 — Colocar os arquivos no seu repositório (Git Bash)

Abra o **Git Bash** na pasta onde você quer trabalhar.

```bash
# 1. Baixe o repositório (ou entre nele, se já tiver)
git clone https://github.com/josewagnerbljr-sys/openops.git
cd openops

# 2. Crie um ramo para a entrega (não mexe na main até você conferir)
git checkout -b cs50-final

# 3. Copie por cima os arquivos recebidos (descompacte openops-cs50-final.zip
#    e copie o CONTEÚDO da pasta openops/ para dentro desta pasta)
#    — ou aplique o patch, se preferir:
git apply --check openops-cs50.patch   # só verifica, não altera nada
git apply openops-cs50.patch

# 4. Veja o que mudou
git status
```

## Passo 2 — Testar localmente antes de subir

```bash
python --version                         # precisa ser 3.10 ou mais novo
# No Git Bash o Python não esconde a digitação de senha; use esta forma (a senha não aparece nem fica no histórico):
read -s -p "Senha do admin (min. 8 caracteres): " OPENOPS_ADMIN_PASSWORD; echo; export OPENOPS_ADMIN_PASSWORD
python openops.py init --admin seu_usuario --demo
unset OPENOPS_ADMIN_PASSWORD
python openops.py serve --open           # abra http://localhost:8000 e teste na mão
# (Ctrl+C para parar)

pip install pytest hypothesis
python -m pytest test_project.py -q       # testes da CLI
cd python && python -m pytest -q          # todos os testes do Python
cd ..
```

> Para rodar também os testes da API FastAPI: `pip install -r requirements-api.txt` antes do `pytest`.
> Se algum teste falhar, **não suba**: me mande a mensagem de erro.

## Passo 3 — Subir para o GitHub

```bash
git add -A
git status                               # confira: NÃO deve aparecer openops.db, openops.log, *.secret
git commit -m "feat: micro-site HTML, CLI openops.py e README CS50"
git push -u origin cs50-final
```

Depois abra o repositório no GitHub, confira o **CI verde** (Actions) e faça o merge do ramo `cs50-final` na `main` (Pull Request).

## Passo 4 — Gravar e publicar o vídeo

1. Siga `docs/VIDEO_ROTEIRO.md` (3 minutos no máximo).
2. Envie para o **YouTube** como **Não listado** (privado **não** vale).
3. Cole a URL no README, na linha `#### Video Demo:`.
4. Preencha o **formulário de submissão do vídeo** indicado na página do projeto final do CS50.

```bash
git add README.md
git commit -m "docs: adiciona URL do vídeo de demonstração"
git push
```

## Passo 5 — Enviar com o submit50

```bash
pip install submit50          # só na primeira vez
cd /caminho/para/openops      # pasta que contém o README.md
submit50 cs50/problems/2026/x/project
```

- Login: seu usuário e senha do GitHub (ao digitar a senha aparecem asteriscos). Se o GitHub pedir token em vez de senha, crie um *personal access token* em GitHub → Settings → Developer settings.
- Tamanho máximo: **100 MB**. O repositório tem menos de 2 MB — mas **apague** antes qualquer `target/` do Rust ou binário do Go, se tiver compilado.
- Se não aparecer nota: reenvie só com o README (`submit50` de novo); o formulário do vídeo **não** precisa ser reenviado.

## Passo 6 — Gradebook e certificado

1. Alguns minutos depois, abra **https://cs50.me/cs50x**.
2. Carregar o gradebook é o que dispara a verificação de conclusão.
3. Clique no link de **CS50 Certificate** no topo do gradebook **antes do prazo**.
4. O certificado edX (se aplicável) é gerado em até 30 dias.

---

## Checklist final

- [ ] `README.md` na raiz, com `#### Video Demo: <URL real>` e `#### Description:`
- [ ] Mais de 750 palavras (o README atual tem ~1.800)
- [ ] Vídeo ≤ 3 min, Não listado, com a abertura exigida
- [ ] Uso de IA citado nos comentários do código **e** descrito honestamente no README
- [ ] `python openops.py serve` funciona numa pasta limpa
- [ ] Testes passando e CI verde
- [ ] `submit50` executado sem erro
- [ ] Gradebook aberto e certificado reivindicado

## Sobre "garantia de aprovação"

Ninguém pode garantir 100% — a nota depende da avaliação do CS50 e de você cumprir as regras de integridade acadêmica. O que este projeto faz é remover os riscos que dá para controlar: requisitos técnicos atendidos, README completo, testes, e um software de verdade que roda. O maior risco restante é humano: **vídeo, URL, e você conseguir explicar o projeto**.
