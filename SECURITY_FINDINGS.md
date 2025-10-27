# Me Feed Security Audit Findings (2025-10-26)

## Critical Severity

### 1. Secrets and Keys Committed to the Repository
**Locations:** `.env`, `.env.prod`, `.env.prod.example`, `config/secrets.json`, `secrets/**`, `backend/secrets/**`, `redis.conf`

**Risk:** All application credentials (PostgreSQL, Redis, SMTP, RapidAPI, TMDB) plus JWT signing keys and encryption material are present in Git. Anyone with repository access can forge tokens, decrypt sensitive data, or access production services. Rotation is mandatory because these secrets must be treated as compromised.

**Remediation:**
- Purge the sensitive files from Git history (e.g., `git filter-repo`).
- Generate new credentials/keys and store them in an external secret manager (Vault, AWS Secrets Manager, Azure Key Vault, etc.).
- Inject secrets at runtime via environment variables or mounted secret files that are excluded from version control.
- Add repository protections to prevent reintroduction of secret files (pre-commit scanning, CI secret scanners).

### 2. Real Netflix Viewing History Committed
**Location:** `NetflixViewingHistory.csv`

**Risk:** Contains actual user viewing history, exposing personal data and breaching privacy regulations (GDPR/CCPA). Treat as a confirmed data leak.

**Remediation:**
- Remove the file from Git history and invalidate any repositories or forks containing it.
- Replace with anonymised sample data if needed for development.
- Notify relevant stakeholders/compliance teams about the exposure and follow incident response procedures.
