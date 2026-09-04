# Manual de Uso da API do OpenOps

Guia passo a passo pra qualquer pessoa usar a API — sem precisar ler código-fonte. Se você chegou aqui pela primeira vez, comece pela seção [Playground público](#playground-público-sem-login), que não exige nenhum cadastro.

## Sumário

- [Playground público (sem login)](#playground-público-sem-login)
- [Rodando a API](#rodando-a-api)
- [Autenticação](#autenticação)
- [Módulo de Produtos](#módulo-de-produtos)
- [Módulo de Clientes](#módulo-de-clientes)
- [Módulo de Estoque](#módulo-de-estoque)
- [SBOM (inventário de dependências)](#sbom-inventário-de-dependências)
- [Erros — como ler](#erros--como-ler)
- [Testando pela interface visual (Swagger)](#testando-pela-interface-visual-swagger)

---

## Playground público (sem login)

Essas rotas não pedem autenticação — dá pra testar assim que a API estiver no ar, sem criar conta.

### Cifrar um texto com AES-256-GCM real

```bash
curl -X POST http://localhost:8000/security-demo/encrypt \
  -H "Content-Type: application/json" \
  -d '{"plaintext": "minha mensagem"}'
```

Devolve `key_hex`, `nonce_hex` e `ciphertext_hex` — cole esses três valores em `/security-demo/decrypt` pra ver o texto original voltar.

### Ver a adulteração sendo detectada, num passo só

```bash
curl -X POST http://localhost:8000/security-demo/tamper-demo \
  -H "Content-Type: application/json" \
  -d '{"plaintext": "dado importante"}'
```

Mostra lado a lado: o dado original decifrando com sucesso, e uma versão com 1 byte alterado de propósito falhando — prova visual de como AEAD protege contra adulteração.

### Quiz sobre os conceitos

```bash
curl http://localhost:8000/security-demo/quiz
```

### Ver o inventário de dependências (SBOM)

```bash
curl http://localhost:8000/sbom
```

---

## Rodando a API

**Com Docker (recomendado):**
```bash
OPENOPS_JWT_SECRET=$(openssl rand -hex 32) docker compose up --build
```

**Sem Docker:**
```bash
cd python
pip install -e ".[dev]"
OPENOPS_JWT_SECRET=$(openssl rand -hex 32) python -m uvicorn openops_api.main:app --reload
```

Em qualquer um dos dois casos, a API sobe em `http://localhost:8000`.

---

## Autenticação

Todo módulo de negócio (Produtos, Clientes, Estoque) exige login. O playground de criptografia e o SBOM, não.

### 1. Criar sua conta

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "seu_usuario", "password": "sua_senha_forte"}'
```

> O **primeiro** usuário registrado no sistema vira `admin` automaticamente. Os próximos entram como `viewer` por padrão (só leitura) — quem for criar/editar/apagar precisa de `role: "operator"` no cadastro.

### 2. Fazer login e pegar o token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "seu_usuario", "password": "sua_senha_forte"}'
```

Resposta:
```json
{"access_token": "eyJhbGci...", "token_type": "bearer"}
```

O token vale por **1 hora**. Depois disso, faça login de novo.

### 3. Usar o token em toda chamada protegida

```bash
curl -H "Authorization: Bearer SEU_TOKEN_AQUI" http://localhost:8000/products
```

### Ver quem você é

```bash
curl -H "Authorization: Bearer SEU_TOKEN_AQUI" http://localhost:8000/auth/me
```

---

## Módulo de Produtos

| Ação | Método | Rota | Papel mínimo |
|---|---|---|---|
| Criar | `POST` | `/products` | `operator` |
| Listar | `GET` | `/products` | qualquer logado |
| Ver um | `GET` | `/products/{id}` | qualquer logado |
| Editar | `PUT` | `/products/{id}` | `operator` |
| Apagar | `DELETE` | `/products/{id}` | `operator` |

```bash
# Criar
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Caneca Personalizada", "price": 29.9, "stock": 15, "category": "presentes"}'

# Listar (opcionalmente filtrando por categoria)
curl -H "Authorization: Bearer $TOKEN" "http://localhost:8000/products?category=presentes"
```

---

## Módulo de Clientes

| Ação | Método | Rota | Papel mínimo |
|---|---|---|---|
| Criar | `POST` | `/customers` | `operator` |
| Listar (com busca) | `GET` | `/customers?search=ana` | qualquer logado |
| Ver um | `GET` | `/customers/{id}` | qualquer logado |
| Editar | `PUT` | `/customers/{id}` | `operator` |
| Apagar | `DELETE` | `/customers/{id}` | `operator` |

```bash
curl -X POST http://localhost:8000/customers \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"name": "Maria Silva", "email": "maria@exemplo.com", "phone": "44999998888"}'
```

E-mail é opcional, mas se informado precisa ser único e válido.

---

## Módulo de Estoque

Registrar um movimento de estoque **atualiza o produto de verdade** — não é um cadastro isolado.

| Ação | Método | Rota | Papel mínimo |
|---|---|---|---|
| Registrar movimento | `POST` | `/inventory/movements` | `operator` |
| Listar movimentos | `GET` | `/inventory/movements?product_id=1` | qualquer logado |
| Ver estoque atual | `GET` | `/inventory/products/{id}/stock` | qualquer logado |

```bash
# movement_type: "in" (entrada), "out" (saída) ou "adjustment" (define valor absoluto)
curl -X POST http://localhost:8000/inventory/movements \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"product_id": 1, "movement_type": "out", "quantity": 5, "reason": "venda #1001"}'
```

Tentar tirar mais estoque do que existe devolve erro `422` com o estoque atual e a quantidade pedida nos `details` — nunca deixa o estoque ficar negativo.

---

## SBOM (inventário de dependências)

```bash
curl http://localhost:8000/sbom
```

Devolve o inventário completo de dependências Python (formato CycloneDX), gerado no momento em que a imagem Docker foi construída. Rodando fora do Docker, provavelmente não existe ainda — a resposta explica isso claramente em vez de dar erro.

---

## Erros — como ler

Todo erro da API segue o mesmo formato:

```json
{
  "error": "validation_error",
  "message": "descrição legível do que deu errado",
  "details": { "campo_especifico": "o que exatamente está errado" }
}
```

| `error` | Código HTTP | Significado |
|---|---|---|
| `validation_error` | 422 | Dado enviado é inválido (ex.: preço negativo) |
| `not_found` | 404 | O recurso não existe |
| `conflict` | 409 | Já existe algo com esse valor único (ex.: nome de produto duplicado) |
| `authorization_error` | 403 | Token ausente, inválido, expirado, ou papel insuficiente |

---

## Testando pela interface visual (Swagger)

Se preferir não usar `curl`, acesse **http://localhost:8000/docs** no navegador — é uma interface interativa onde dá pra testar toda rota clicando, sem escrever nenhum comando.

1. Abra `/auth/register`, clique **Try it out**, preencha, **Execute**.
2. Abra `/auth/login`, mesma coisa, copie o `access_token` da resposta.
3. Clique no botão verde **Authorize** 🔒 no topo da página, cole o token, confirme.
4. Agora todas as rotas protegidas já usam esse token automaticamente — só clicar **Try it out** → **Execute** em qualquer uma.

> O token expira em 1 hora. Se uma rota que antes funcionava passar a dar erro 403, é só repetir os passos 2 e 3.
