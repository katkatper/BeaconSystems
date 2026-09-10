# Security and repository hygiene

## Credentials

- Never commit `.env` files or place them in source archives.
- Commit only sanitized `.env.example` templates with placeholder values.
- Treat credentials included in an archive, log, screenshot, or shared message as exposed. Rotate them at their issuing systems; deleting the archive does not revoke them.
- Keep production secrets in the deployment platform's secret manager.

## Repository contents

Do not commit or package installed dependencies, virtual environments, build output, caches, local uploads, evidence, or repository metadata. This includes `node_modules`, `.venv`, `venv`, `bin`, `obj`, `dist`, `uploads`, `__pycache__`, and `.git`.

Before committing or preparing a source package, run:

```powershell
python scripts/check_repository_hygiene.py
git status --short
```

Create source archives from tracked files instead of zipping the working directory:

```powershell
git archive --format=zip --output BeaconSystems-source.zip HEAD
```

The repository-hygiene workflow performs the tracked-file check on every push and pull request.
