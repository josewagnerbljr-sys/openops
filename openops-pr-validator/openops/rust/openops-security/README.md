# openops-security (Rust)

Camada Security do OpenOps — Camada 1 ("Data") descrita no [ARCHITECTURE.md](../../ARCHITECTURE.md): criptografia autenticada AES-256-GCM (AEAD), com nonce único por operação e falha explícita em caso de adulteração.

Rust foi escolhido para esta camada especificamente pela garantia de segurança de memória em tempo de compilação — uma propriedade valiosa em código de criptografia.

## Build

```bash
cargo build --release
```

## Rodar os testes

```bash
cargo test
```

## Uso básico

```rust
use openops_security::{generate_key, encrypt, decrypt};

let key = generate_key();
let sealed = encrypt(b"dados sensiveis", &key)?;
let recovered = decrypt(&sealed, &key)?;
assert_eq!(recovered, b"dados sensiveis");
```

## Garantias

- Nonce de 96 bits gerado por CSPRNG do SO em **cada** chamada de `encrypt` — nunca reaproveitado.
- `decrypt` nunca retorna dado parcial: se a tag de autenticação não conferir, retorna `Err(SecurityError::DecryptionFailed)`.
- Chave de tamanho incorreto é rejeitada antes de qualquer operação criptográfica.

## Próximos passos (Fase 6 do roadmap)

- Camada 2 (Storage/Secrets): hierarquia e rotação de chaves.
- Camada 3 (Access/Runtime): autenticação, RBAC, rate limiting, auditoria.
