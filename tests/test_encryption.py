"""Encryption helper tests."""

from __future__ import annotations

from cryptography.fernet import Fernet

from src.utils.encryption import decrypt_text, encrypt_text


def test_encrypt_decrypt_roundtrip():
    key = Fernet.generate_key()
    token = encrypt_text("Sector 7", key)
    assert token != "Sector 7"
    assert decrypt_text(token, key) == "Sector 7"
