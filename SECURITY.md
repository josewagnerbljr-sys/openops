# Política de Segurança

## Reportando uma vulnerabilidade

Se você encontrar uma vulnerabilidade de segurança no OpenOps, **não abra uma issue pública**. Em vez disso:

1. Envie um e-mail para **consultoriablanco8@gmail.com** com o assunto `[SECURITY] <resumo curto>`.
2. Descreva o problema, o impacto potencial e, se possível, passos para reproduzir.
3. Você receberá uma confirmação de recebimento em até 5 dias úteis.

Pedimos que você não divulgue publicamente a vulnerabilidade até que uma correção esteja disponível.

## Escopo

Este processo cobre o código deste repositório (`python/`, `go/`, `rust/`). Não cobre serviços de terceiros, infraestrutura de hospedagem de forks individuais, nem qualquer componente proprietário mencionado no [ARCHITECTURE.md](ARCHITECTURE.md) que fique fora deste repositório público.

Para uma análise sistemática de ameaças (metodologia STRIDE) — o que já está mitigado e o que é risco conscientemente aceito, com plano de quando será revisitado — veja [THREAT_MODEL.md](THREAT_MODEL.md).

## Validação automática de Pull Requests

Todo PR passa por três camadas automáticas antes de revisão humana:

1. **Build e testes** (`ci.yml`, jobs `python`/`go`/`rust`) — roda sob o evento `pull_request`, sem acesso a secrets nem permissão de escrita, mesmo para PRs de forks não confiáveis.
2. **Scanner de segredos** (`openops-cli secscan`, job `security-scan` em `ci.yml`) — varre o diff em busca de credenciais reais (chaves AWS, tokens do GitHub, chaves privadas PEM, etc.).
3. **Comentário e decisão** (`pr-comment.yml`) — roda separadamente, em contexto confiável (nunca executa código do fork), lê o resultado das etapas acima e:
   - Se um segredo de **alta confiança** for encontrado: comenta a explicação, adiciona o label `security-hold` e **fecha o PR automaticamente**.
   - Caso contrário: comenta um resumo de pass/fail por linguagem, com orientação de como corrigir se algo falhar.

**O bloqueio de um usuário nunca é automático.** Só o mantenedor pode disparar isso, comentando `/block-contributor <username>` em um PR ou issue (`block-contributor.yml`) — requer um Personal Access Token com escopo `user:block` configurado como secret `USER_BLOCK_TOKEN`.

## O que esperar

- Vulnerabilidades relacionadas à camada Security (`rust/openops-security`) — como reutilização de nonce, falhas de autenticação AEAD, ou vazamento de material de chave — recebem prioridade máxima.
- Não fazemos afirmações de invulnerabilidade absoluta. O objetivo declarado no projeto é tornar adulteração **detectável**, falhas **rastreáveis** e recuperação **confiável** — não prometer o que nenhum software local pode garantir contra quem tem controle total do ambiente.

## Versões suportadas

Enquanto o projeto estiver em fase `0.x` (pré-1.0), apenas a branch `main` recebe correções de segurança.
