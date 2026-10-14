# Manual do micro-site OpenOps (para quem não programa)

## 1. Ligar o sistema

Na pasta do OpenOps, abra o terminal (ou Git Bash) e digite:

```bash
python openops.py serve --open
```

O navegador abre em **http://localhost:8000**. Para desligar, volte ao terminal e aperte **Ctrl+C**.

**Primeira vez?** Rode antes `python openops.py init --admin seu_usuario` (ele pede uma senha) — ou, na primeira abertura, a própria página pede para você criar o administrador (só funciona no computador onde o sistema está instalado). Quer ver tudo funcionando com dados de exemplo? Acrescente `--demo`.

## 2. Perfis de acesso

| Perfil | Pode |
|---|---|
| **Consulta** | Ver painel, produtos, movimentações, clientes; baixar planilhas |
| **Operador** | Tudo de Consulta + cadastrar produtos, registrar entradas/saídas, corrigir contagem, remover produtos, gerenciar clientes |
| **Administrador** | Tudo de Operador + criar usuários, mudar perfis, apagar usuários |

O sistema nunca fica sem administrador: o último não pode ser rebaixado nem apagado.

## 3. Tarefas do dia a dia

| Quero… | Faça |
|---|---|
| **Cadastrar produto** | Produtos → **Novo produto** → nome, preço, categoria e estoque inicial (opcional) |
| **Dar entrada** (chegou mercadoria) | Na linha do produto, digite a quantidade e clique **+ Entrada** |
| **Dar saída** (vendeu/perdeu) | Digite a quantidade e clique **− Saída**. Se pedir mais do que existe, o sistema avisa e não grava nada |
| **Entrada com lote e validade** | **Mais → Entrada com lote e validade** |
| **Corrigir contagem** (inventário físico) | **Mais → Corrigir contagem** e informe a quantidade realmente contada |
| **Mudar nome/preço** | **Mais → Editar** (o estoque só muda por entrada/saída/correção) |
| **Remover produto** | **Mais → Remover**. Sem histórico: apaga. Com histórico: **arquiva** (some da lista, mas as movimentações antigas ficam) |
| **Ver o histórico** | Aba **Movimentações** (filtre por produto) |
| **Ver o que está acabando/vencendo** | Aba **Painel** |
| **Planilha para Excel** | **Baixar planilha (CSV)** em Produtos ou Movimentações |
| **Trocar minha senha** | **Senha**, no topo |

**Estoque baixo** = 5 unidades ou menos. **Lotes perto do vencimento** = validade nos próximos 30 dias, mostrando só produtos que ainda têm saldo.

## 4. Usar em outros computadores da loja

Por padrão o sistema só atende o próprio computador (mais seguro). Para acessar de outros aparelhos da mesma rede:

```bash
python openops.py serve --host 0.0.0.0 --port 8000
```

Os outros acessam `http://IP-DO-COMPUTADOR:8000`. Use só em rede de confiança — o tráfego **não é criptografado**. Para internet, coloque o sistema atrás de um proxy com HTTPS.

## 5. Avisos automáticos de validade

```bash
python openops.py expiry --days 30           # lista lotes que vencem em até 30 dias
python openops.py expiry --days 30 --json    # formato para outros programas
```

No Windows, o **Agendador de Tarefas** pode rodar isso todo dia. (`--fail-on-found` faz o comando terminar com código 1 quando há lotes, útil em scripts.)

## 6. Backup

Tudo fica em **um arquivo**: `openops.db` (mais `openops.db.secret`, a chave das sessões). Copie esses arquivos com o sistema desligado e está feito. O arquivo `openops.log` registra quem fez o quê.

## 7. Problemas comuns

| Mensagem | O que fazer |
|---|---|
| "A porta já está em uso" | Outro programa usa a 8000. Rode com `--port 8080` |
| "Muitas tentativas; aguarde…" | Senha errada 5 vezes seguidas. Espere 5 minutos |
| "Sua sessão terminou" | A sessão dura 8 horas. Entre novamente |
| Esqueci a senha | No terminal: `python openops.py reset-password seu_usuario` (pede a nova senha). Só funciona para quem tem acesso ao computador do sistema |
