# Roteiro do vídeo de demonstração (máximo 3 minutos)

Regras do CS50: **≤ 3 min**, YouTube **não listado** (privado não vale), e a abertura **precisa** mostrar: título do projeto, seu nome, usuários do **GitHub** e do **edX**, **cidade e país**, e a **data da gravação**.

Dica: grave a tela (OBS Studio, Xbox Game Bar `Win+G`, ou a gravação do próprio YouTube) e fale em cima. Pode ser em português ou inglês; inglês facilita a avaliação.

| Tempo | Na tela | O que dizer (adapte com suas palavras) |
|---|---|---|
| 0:00–0:15 | Slide simples: **OpenOps — Stock-control micro-site**, seu nome, `github.com/josewagnerbljr-sys`, usuário edX, **Paiçandu, Paraná, Brasil**, data de hoje | "Olá, eu sou José Wagner Blanco Júnior, de Paiçandu, Paraná, Brasil. Este é o OpenOps, meu projeto final do CS50. Gravado em ‹data›." |
| 0:15–0:40 | Terminal com `python openops.py init --admin ... --demo` e `serve --open` | "O problema: o sistema original só tinha uma API, inutilizável para quem recebe a mercadoria. Agora são dois comandos e abre uma página no navegador. Não precisa instalar nada além do Python." |
| 0:40–1:25 | Painel → Produtos. Clique em **+ Entrada** e **− Saída**; mostre o medidor mudando e o aviso "estoque insuficiente" | "Entrada e saída são um clique na própria linha. O sistema nunca deixa o estoque ficar negativo." |
| 1:25–1:50 | **Mais → Remover** em um produto com histórico; depois a aba Movimentações | "Produto com histórico é arquivado, não apagado: a auditoria continua intacta." |
| 1:50–2:15 | Dashboard (estoque baixo, vencimentos), Usuários (papéis), baixar CSV | "Papéis de consulta, operador e administrador; relatórios em CSV; alertas de estoque baixo e validade." |
| 2:15–2:45 | Editor de código: `python/openops_web/app.py` (função `handle`) e o teste de concorrência `test_concurrent_removals_never_oversell` rodando | "Explique COM SUAS PALAVRAS, só o que você entendeu e fez. Sugestão de conteúdo: a lógica é uma função que recebe requisição e devolve resposta, então dá para testar sem rede. Durante o desenvolvimento com a IA foi encontrado e corrigido um bug de concorrência (duas vendas simultâneas podiam vender estoque inexistente); hoje um teste dispara 120 vendas em 16 threads. Diga claramente o que foi feito pela IA e o que foi feito por você." |
| 2:45–3:00 | Slide final | "Usei IA (Claude) como assistente de implementação, conforme a política do CS50, e está citado no código e no README. Obrigado!" |

## Antes de gravar
- [ ] Rode `python openops.py init --admin demo --demo` numa pasta nova, para os dados de exemplo aparecerem.
- [ ] Feche abas e notificações; aumente o zoom do navegador (125%).
- [ ] Ensaie uma vez com cronômetro. Se passar de 3:00, corte a parte do CSV.
- [ ] Depois de publicar: abra o link em janela anônima para conferir que **não está privado**.
