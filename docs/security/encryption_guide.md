# Encryption Guide

SADAR uses Fernet-compatible symmetric encryption helpers for sensitive local fields.

Guidelines:
- Generate one key per environment.
- Store keys outside Git, preferably in a secret manager.
- Rotate keys on operator changes or suspected exposure.
- Never commit `.env`, `*.key`, or local database files.

For local development:

```bash
python scripts/generate_key.py > config/keys/master.key
```
