# Política de Segurança

## Reportando uma vulnerabilidade

Se você encontrar uma vulnerabilidade de segurança no OpenOps, **não abra uma issue pública**. Em vez disso:

1. Envie um e-mail para **consultoriablanco8@gmail.com** com o assunto `[SECURITY] <resumo curto>`.
2. Descreva o problema, o impacto potencial e, se possível, passos para reproduzir.
3. Você receberá uma confirmação de recebimento em até 5 dias úteis.

Pedimos que você não divulgue publicamente a vulnerabilidade até que uma correção esteja disponível.

## Escopo

Este processo cobre o código deste repositório (`python/`, `go/`, `rust/`). Não cobre serviços de terceiros, infraestrutura de hospedagem de forks individuais, nem qualquer componente proprietário mencionado no [ARCHITECTURE.md](ARCHITECTURE.md) que fique fora deste repositório público.

## O que esperar

- Vulnerabilidades relacionadas à camada Security (`rust/openops-security`) — como reutilização de nonce, falhas de autenticação AEAD, ou vazamento de material de chave — recebem prioridade máxima.
- Não fazemos afirmações de invulnerabilidade absoluta. O objetivo declarado no projeto é tornar adulteração **detectável**, falhas **rastreáveis** e recuperação **confiável** — não prometer o que nenhum software local pode garantir contra quem tem controle total do ambiente.

## Versões suportadas

Enquanto o projeto estiver em fase `0.x` (pré-1.0), apenas a branch `main` recebe correções de segurança.
