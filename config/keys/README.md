# Key directory

Runtime encryption keys belong here for local development only.

Rules:
- Do not commit real key material.
- `*.key` files are ignored by `.gitignore`.
- Generate fresh keys per environment.
- Prefer environment variables or a managed secret store in production.
