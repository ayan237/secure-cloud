import pytest
from backend.encryption import generate_key, encrypt_block, decrypt_block

def test_key_generation():
    key = generate_key()
    assert isinstance(key, bytes)
    assert len(key) == 32

def test_encrypt_decrypt_roundtrip():
    key = generate_key()
    original_data = b"SecureCloud AES-256-GCM encryption verification test data block."
    nonce, ciphertext = encrypt_block(original_data, key)
    
    assert len(nonce) == 12
    assert ciphertext != original_data
    
    decrypted_data = decrypt_block(nonce, ciphertext, key)
    assert decrypted_data == original_data

def test_decrypt_invalid_key_fails():
    key1 = generate_key()
    key2 = generate_key()
    original_data = b"Secret data"
    nonce, ciphertext = encrypt_block(original_data, key1)
    
    with pytest.raises(Exception):
        decrypt_block(nonce, ciphertext, key2)
