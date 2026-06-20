# Key Management Policy

- Development keys are local only and ignored by Git.
- Production keys must come from environment variables or a managed secret store.
- Access to production keys should be limited to operators who deploy SADAR.
- Rotate keys when staff access changes, a host is rebuilt, or exposure is suspected.
- Backups containing encrypted data must be protected with the same access controls.
