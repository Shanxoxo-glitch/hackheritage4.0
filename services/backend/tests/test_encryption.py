from app.services.encryption import encrypt_pii, decrypt_pii

def test_aes256_pii_encryption_roundtrip():
    original_name = "Ramesh Kumar"
    original_phone = "+919876543210"

    encrypted_name = encrypt_pii(original_name)
    encrypted_phone = encrypt_pii(original_phone)

    assert encrypted_name != original_name
    assert encrypted_phone != original_phone

    decrypted_name = decrypt_pii(encrypted_name)
    decrypted_phone = decrypt_pii(encrypted_phone)

    assert decrypted_name == original_name
    assert decrypted_phone == original_phone

def test_encryption_handles_none():
    assert encrypt_pii(None) is None
    assert decrypt_pii(None) is None
