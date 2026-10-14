//! openops-security
//! =================
//!
//! Implementação da "Camada 1 — Data" descrita no item 9 (OpenOps
//! Security) do documento mestre: criptografia autenticada (AEAD) usando
//! AES-256-GCM, com nonce aleatório de 96 bits gerado por chamada — nunca
//! reutilizado — e falha explícita (nunca silenciosa) quando a
//! autenticação do texto cifrado não confere.
//!
//! Rust foi escolhido especificamente para esta camada porque o
//! compilador garante, em tempo de compilação, ausência de buffer
//! overflows e uso de memória após liberação — uma propriedade
//! particularmente valiosa em código de criptografia.

use aes_gcm::aead::{Aead, KeyInit, OsRng};
use aes_gcm::{AeadCore, Aes256Gcm, Key, Nonce};
use thiserror::Error;

pub const KEY_LEN: usize = 32; // AES-256
const NONCE_LEN: usize = 12; // 96 bits, tamanho padrão do GCM

#[derive(Debug, Error, PartialEq, Eq)]
pub enum SecurityError {
    #[error("chave inválida: esperado {KEY_LEN} bytes, recebido {0} bytes")]
    InvalidKeyLength(usize),

    #[error("texto cifrado inválido ou truncado (menor que o nonce)")]
    CiphertextTooShort,

    #[error("falha na criptografia (AEAD)")]
    EncryptionFailed,

    #[error("falha na decriptografia: dado corrompido, chave incorreta ou adulteração detectada")]
    DecryptionFailed,
}

/// Gera uma nova chave AES-256 aleatoriamente segura (CSPRNG do SO).
pub fn generate_key() -> [u8; KEY_LEN] {
    let key = Aes256Gcm::generate_key(OsRng);
    key.into()
}

/// Cifra `plaintext` com AES-256-GCM sob `key`.
///
/// O retorno é `nonce || ciphertext_com_tag`, pronto para armazenamento
/// ou transporte. Cada chamada gera um nonce novo — nunca reaproveitar
/// nonce com a mesma chave é a invariante mais importante do GCM.
pub fn encrypt(plaintext: &[u8], key: &[u8]) -> Result<Vec<u8>, SecurityError> {
    let key = validate_key(key)?;
    let cipher = Aes256Gcm::new(key);
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng);

    let ciphertext = cipher
        .encrypt(&nonce, plaintext)
        .map_err(|_| SecurityError::EncryptionFailed)?;

    let mut output = Vec::with_capacity(NONCE_LEN + ciphertext.len());
    output.extend_from_slice(nonce.as_slice());
    output.extend_from_slice(&ciphertext);
    Ok(output)
}

/// Decifra um valor produzido por [`encrypt`]. Retorna erro (nunca dado
/// parcial) se a tag de autenticação não conferir.
pub fn decrypt(sealed: &[u8], key: &[u8]) -> Result<Vec<u8>, SecurityError> {
    let key = validate_key(key)?;

    if sealed.len() < NONCE_LEN {
        return Err(SecurityError::CiphertextTooShort);
    }

    let (nonce_bytes, ciphertext) = sealed.split_at(NONCE_LEN);
    let nonce = Nonce::from_slice(nonce_bytes);
    let cipher = Aes256Gcm::new(key);

    cipher
        .decrypt(nonce, ciphertext)
        .map_err(|_| SecurityError::DecryptionFailed)
}

fn validate_key(key: &[u8]) -> Result<&Key<Aes256Gcm>, SecurityError> {
    if key.len() != KEY_LEN {
        return Err(SecurityError::InvalidKeyLength(key.len()));
    }
    Ok(Key::<Aes256Gcm>::from_slice(key))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_encrypt_decrypt() {
        let key = generate_key();
        let plaintext = b"dados sensiveis do OpenOps";

        let sealed = encrypt(plaintext, &key).expect("encrypt deve funcionar");
        let recovered = decrypt(&sealed, &key).expect("decrypt deve funcionar");

        assert_eq!(recovered, plaintext);
    }

    #[test]
    fn two_encryptions_never_share_a_nonce() {
        let key = generate_key();
        let sealed_a = encrypt(b"mensagem", &key).unwrap();
        let sealed_b = encrypt(b"mensagem", &key).unwrap();

        assert_ne!(&sealed_a[..NONCE_LEN], &sealed_b[..NONCE_LEN]);
    }

    #[test]
    fn tampering_is_detected() {
        let key = generate_key();
        let mut sealed = encrypt(b"conteudo integro", &key).unwrap();

        let last = sealed.len() - 1;
        sealed[last] ^= 0xFF; // corrompe um byte da tag/ciphertext

        let result = decrypt(&sealed, &key);

        assert_eq!(result, Err(SecurityError::DecryptionFailed));
    }

    #[test]
    fn wrong_key_fails_to_decrypt() {
        let key_a = generate_key();
        let key_b = generate_key();
        let sealed = encrypt(b"segredo", &key_a).unwrap();

        let result = decrypt(&sealed, &key_b);

        assert_eq!(result, Err(SecurityError::DecryptionFailed));
    }

    #[test]
    fn rejects_invalid_key_length() {
        let short_key = [0u8; 16];

        let result = encrypt(b"x", &short_key);

        assert_eq!(result, Err(SecurityError::InvalidKeyLength(16)));
    }

    #[test]
    fn rejects_truncated_ciphertext() {
        let key = generate_key();

        let result = decrypt(&[0u8; 4], &key);

        assert_eq!(result, Err(SecurityError::CiphertextTooShort));
    }
}
