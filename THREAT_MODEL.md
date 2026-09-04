# Threat Model — OpenOps

**Metodologia:** STRIDE (Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege) — desenvolvida pela Microsoft, padrão de facto para modelagem de ameaças em engenharia de software.

**Escopo desta versão:** o repositório público `openops` no estado atual (Fase 0–2 do [ROADMAP](ROADMAP.md) concluídas). Este documento será revisado a cada fase que altere a superfície de ataque do sistema — não é um artefato estático.

**O que este documento não é:** uma auditoria de segurança externa, nem uma garantia de invulnerabilidade. É uma análise sistemática, honesta sobre o que está mitigado hoje e o que é risco conscientemente aceito — alinhado ao princípio de "honestidade técnica" do [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 1. Visão geral do sistema e fronteiras de confiança

```
┌─────────────────────┐     fork + PR      ┌──────────────────────────┐
│ Contribuidor externo │ ─────────────────► │ ci.yml (pull_request)    │  ZONA NÃO CONFIÁVEL
│ (não confiável)      │                    │ build/test/secscan       │  (sem secrets, sem write)
└─────────────────────┘                    └──────────┬───────────────┘
                                                        │ artefato (JSON)
                                                        ▼
                                            ┌──────────────────────────┐
                                            │ pr-comment.yml            │  ZONA CONFIÁVEL
                                            │ (workflow_run)             │  (tem secrets, write)
                                            │ NUNCA executa código do PR │  NUNCA faz checkout do fork
                                            └──────────┬───────────────┘
                                                        │ comenta / fecha PR
                                                        ▼
┌──────────────────┐   HTTP    ┌──────────────────┐   SQL   ┌──────────────────┐
│ Cliente da API    │ ───────► │ openops_api        │ ─────► │ SQLite (local)     │
│ (sem autenticação  │          │ (FastAPI)          │         │ arquivo em disco   │
│  hoje — ver §7)    │          └──────────────────┘         └──────────────────┘

┌──────────────────┐
│ Mantenedor         │ ── comando /block-contributor ──► block-contributor.yml (só roda p/ repository_owner)
└──────────────────┘
```

A fronteira de confiança mais crítica do sistema hoje é a que separa **código vindo de um fork** (não confiável, pode ser malicioso) da **execução com privilégios de escrita e acesso a secrets** (confiável). Essa fronteira é o que motivou a separação em dois workflows (`ci.yml` + `pr-comment.yml`) descrita no `SECURITY.md`.

## 2. Ativos a proteger

| Ativo | Por quê importa |
|---|---|
| `secrets.GITHUB_TOKEN` e `secrets.USER_BLOCK_TOKEN` | Acesso de escrita ao repositório / capacidade de bloquear usuários no GitHub |
| Chaves de criptografia geradas por `openops-security` | Confidencialidade de qualquer dado cifrado com elas |
| Dados armazenados no SQLite (`openops.db`) | Dados de negócio (produtos, e futuramente clientes/vendas) |
| Integridade do histórico de commits e do pipeline de CI | Confiança de quem usa/faz fork do projeto |
| Disponibilidade da API e do CLI | Uso contínuo por quem depende do sistema |

## 3. Atores e fontes de ameaça

- **Contribuidor externo mal-intencionado**: abre PR de um fork tentando executar código com privilégio, vazar secrets, ou introduzir backdoor.
- **Operador da API sem autenticação** (hoje, qualquer chamador): a API não tem controle de acesso ainda — tratado como risco aceito, não ignorado (§7).
- **Dependência de terceiro comprometida** (supply chain): um pacote PyPI/crates.io/Go module malicioso ou sequestrado.
- **O próprio mantenedor**: erro humano (commit de segredo, configuração incorreta) — mitigado por automação, não por confiança.

## 4. Análise STRIDE por componente

### 4.1 Pipeline de CI/CD (`ci.yml`, `pr-comment.yml`, `block-contributor.yml`)

| Categoria | Ameaça concreta | Status |
|---|---|---|
| **S**poofing | Um PR forjar a autoria de outro usuário | Fora do nosso controle — depende da autenticação do GitHub; não mitigável por nós |
| **T**ampering | PR malicioso alterar `ci.yml`/`pr-comment.yml` para rodar código arbitrário com secrets (*pwn request*) | ✅ Mitigado — `ci.yml` roda sob `pull_request` (sem secrets, sem write); `pr-comment.yml` roda sob `workflow_run`, nunca faz checkout do fork |
| **R**epudiation | Ação do CI sem rastro de quem/por quê | ✅ Mitigado parcialmente — todo comentário automático e todo fechamento de PR fica registrado no histórico do próprio PR no GitHub |
| **I**nformation Disclosure | Segredo real (chave de API, token) vazado num PR | ✅ Mitigado — `secscan` roda em todo PR e rejeita automaticamente credenciais de alta confiança (ver `SECURITY.md`) |
| **D**enial of Service | PR gigante ou com milhares de arquivos travando o `secscan`/CI | ⚠️ Mitigado parcialmente — `secscan` ignora arquivos >300 KB e conteúdo binário; não há limite explícito de *número* de arquivos por PR |
| **E**levation of Privilege | Usuário não-mantenedor conseguir disparar `/block-contributor` | ✅ Mitigado — o workflow checa `github.event.comment.user.login == github.repository_owner` antes de agir |

### 4.2 Camada Security (`rust/openops-security`)

| Categoria | Ameaça concreta | Status |
|---|---|---|
| **T**ampering | Ciphertext adulterado ser aceito como válido | ✅ Mitigado — AES-256-GCM é AEAD; qualquer byte alterado (nonce, ciphertext ou tag) falha a autenticação, provado por teste de propriedade (`corrupting_any_single_byte_breaks_decryption`) |
| **I**nformation Disclosure | Reuso de nonce quebrando a confidencialidade do GCM | ✅ Mitigado — nonce gerado por CSPRNG do SO a cada chamada de `encrypt`, nunca reaproveitado; provado por teste de propriedade (`nonce_is_never_reused_across_encryptions`) |
| **I**nformation Disclosure | Chave de criptografia armazenada em texto claro | ⚠️ Risco aceito hoje — `generate_key()` devolve a chave em memória; **gestão de chaves (rotação, cofre, HSM) é escopo da Fase 6 (Security completa)**, ainda não implementada |
| **D**enial of Service | Entrada gigante travando a cifra | Não mitigado explicitamente — não há limite de tamanho de `plaintext` na função `encrypt`; risco baixo (uso é local, não exposto via rede diretamente hoje) |

### 4.3 API HTTP (`openops_api`)

| Categoria | Ameaça concreta | Status |
|---|---|---|
| **S**poofing / **E**levation of Privilege | Qualquer chamador conseguir criar/editar/apagar produtos, sem autenticação | ✅ Mitigado — autenticação JWT (Argon2id para senha) e RBAC (viewer/operator/admin) obrigatórios em toda rota de negócio; leitura exige login, escrita exige "operator"+ |
| **T**ampering | Injeção SQL via parâmetros da API | ✅ Mitigado — todo acesso a banco em `openops_core/db.py` usa parâmetros posicionais (`?`) do `sqlite3`, nunca concatenação de string |
| **I**nformation Disclosure | Stack trace ou detalhe interno vazando em resposta de erro | ✅ Mitigado — todo erro de domínio passa por `OpenOpsError.to_dict()`, que expõe só `error`/`message`/`details` estruturados, nunca traceback; erros não mapeados (bugs reais) ainda cairiam no handler padrão do FastAPI — não coberto por teste ainda |
| **I**nformation Disclosure | Senha de usuário armazenada em texto claro ou hash fraco | ✅ Mitigado — Argon2id (via `argon2-cffi`), recomendado atualmente pela OWASP; nunca comparação em texto claro |
| **D**enial of Service | Ausência de rate limiting | ⚠️ Risco aceito — nenhum rate limiting implementado ainda |
| **R**epudiation | Chamadas à API sem rastro de quem fez o quê | ⚠️ Parcialmente mitigado — o token JWT identifica o usuário em cada requisição (logs de acesso já sabem "quem"), mas não há um log de auditoria estruturado por operação ainda (planejado para a Fase 7 — Maintenance) |

### 4.4 CLI (`go/openops-cli`)

| Categoria | Ameaça concreta | Status |
|---|---|---|
| **T**ampering | Binário do CLI adulterado sendo distribuído como se fosse oficial | ✅ Mitigado — releases (`v*`) são assinados via Sigstore/cosign (assinatura keyless, ligada ao workflow/commit de origem, com log público no Rekor); veja instruções de verificação nas notas de cada release |
| **I**nformation Disclosure | `docgen`/`secscan` vazando conteúdo de arquivos sensíveis não intencionalmente no relatório HTML | ⚠️ Risco aceito e por design — a ferramenta lê o que está no diretório apontado; cabe ao usuário não apontá-la para diretórios com segredos. `secscan` existe justamente para pegar esse tipo de vazamento antes do commit |

## 5. Resumo — mitigado vs. aceito

**Mitigado ativamente (com código e/ou teste comprovando):**
- Pwn request no CI (separação `pull_request` / `workflow_run`)
- Vazamento de segredo em PR (scanner automático + rejeição)
- Bloqueio de usuário só pelo mantenedor
- Adulteração de dado cifrado (AEAD, testado com property-based testing)
- Reuso de nonce (testado com property-based testing)
- Injeção SQL (parâmetros preparados em toda a camada de banco)
- Vazamento de stack trace em erro de API (erros estruturados)
- **Autenticação e RBAC na API** (JWT + Argon2id + papéis viewer/operator/admin) — fecha o item que antes era o principal risco aceito da API (ver §4.3 abaixo, atualizado)

**Risco conscientemente aceito, com plano declarado:**
- Rate limiting — Fase 6
- Log de auditoria estruturado por operação — Fase 7 (Maintenance)
- Limite de número de arquivos por PR no `secscan` — sem data definida

**Implementado, mas ainda não validado em produção real:**
- Assinatura de binários de release via Sigstore/cosign (`release.yml`) — build cross-plataforma testado localmente com sucesso; a assinatura keyless em si só pode ser validada quando uma tag `v*` real for enviada ao GitHub (ambiente de desenvolvimento não tem acesso ao runtime OIDC do GitHub Actions)

## 6. Fora de escopo

- Segurança da infraestrutura de hospedagem de um fork individual (responsabilidade de quem hospeda).
- Componentes proprietários mencionados no `ARCHITECTURE.md` que ficam fora deste repositório público.
- Segurança física ou da conta pessoal do GitHub do mantenedor.

## 7. Sobre autenticação e chave JWT

A API exige autenticação (JWT) e RBAC (papéis `viewer`/`operator`/`admin`) em toda rota de negócio desde esta versão. **Importante para quem for rodar em produção**: defina `OPENOPS_JWT_SECRET` com um valor forte e fixo (ex.: `openssl rand -hex 32`) — se essa variável não for definida, uma chave aleatória é gerada a cada reinício do processo, e **todo token emitido antes do reinício vira inválido**. Isso é intencional (evita rodar com uma chave fraca/padrão por engano em produção), mas exige essa configuração explícita.

## 8. Rotas públicas intencionais (`/security-demo/*`, `/sbom`)

Duas famílias de rota ficam deliberadamente **fora** da autenticação, por design — não é uma omissão:

- **`/security-demo/*`** — playground educacional de AES-256-GCM. Cada chamada gera uma chave efêmera nova, nunca reaproveitada e nunca relacionada a nenhum segredo real do sistema; não há dado de negócio nem segredo algum em risco. Implementação em Python (`cryptography`), independente do crate `openops-security` (Rust) usado no resto da arquitetura.
- **`/sbom`** — inventário de dependências (CycloneDX), gerado em tempo de build da imagem Docker. Informação já pública em qualquer release; expor via API só facilita a consulta, não adiciona superfície de ataque nova.

## 9. Sobre contribuir com este documento

Encontrou uma ameaça não listada aqui, ou uma mitigação que ficou desatualizada? Veja o processo de reporte em [SECURITY.md](SECURITY.md) — para riscos de segurança real, não abra uma issue pública. Para sugestões de melhoria deste documento em si, um PR normal é bem-vindo.
