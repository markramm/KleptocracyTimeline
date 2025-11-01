# Security Guidelines

## Overview

This document outlines security considerations and hardening steps for the Kleptocracy Timeline project, particularly for production deployments.

## Environment Variables

### Configuration

All sensitive configuration should be stored in environment variables, **never** hardcoded in source files.

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Generate secure random keys:
   ```bash
   # Generate API key
   python3 -c "import secrets; print('RESEARCH_MONITOR_API_KEY=' + secrets.token_urlsafe(32))"

   # Generate secret key
   python3 -c "import secrets; print('RESEARCH_MONITOR_SECRET=' + secrets.token_hex(32))"
   ```

3. Set file permissions (Unix/Linux/macOS):
   ```bash
   chmod 600 .env
   ```

4. Configure required variables in `.env`:
   - `RESEARCH_MONITOR_API_KEY` - Strong random value (minimum 32 characters)
   - `RESEARCH_MONITOR_SECRET` - Strong random value (minimum 32 characters)
   - `GITHUB_TOKEN` - Personal access token with `repo` scope only
   - `TIMELINE_REPO_URL` - Your timeline repository URL

### Verification

The `.env` file is already in `.gitignore` and will **never** be committed to version control.

## Hardcoded Credentials (Development Only)

⚠️ **WARNING**: The following files contain hardcoded credentials for development/testing purposes only. These **MUST NOT** be used in production.

### Files with Hardcoded Test Credentials

1. **research_client.py** (Line ~48)
   ```python
   # DEVELOPMENT ONLY
   def __init__(self, base_url: Optional[str] = None, api_key: str = "test-key"):
   ```
   **Production Fix**: Always pass `api_key` parameter or set `RESEARCH_MONITOR_API_KEY` environment variable.

2. **research_api.py** (Line ~32)
   ```python
   # DEVELOPMENT ONLY
   self.api_key: str = api_key or os.getenv('RESEARCH_MONITOR_API_KEY', 'test') or 'test'
   ```
   **Production Fix**: Set `RESEARCH_MONITOR_API_KEY` environment variable. Never use 'test' default.

3. **research_monitor/test_app_v2.py** (Multiple lines)
   ```python
   # TEST FILE ONLY - Not used in production
   os.environ['RESEARCH_MONITOR_API_KEY'] = 'test-key'
   headers={'X-API-Key': 'test-key'}
   ```
   **Status**: Test file only, acceptable for development.

### Production Deployment Checklist

Before deploying to production:

- [ ] Copy `.env.example` to `.env`
- [ ] Generate strong `RESEARCH_MONITOR_API_KEY` (min 32 chars)
- [ ] Generate strong `RESEARCH_MONITOR_SECRET` (min 32 chars)
- [ ] Set `DEBUG=false` in `.env`
- [ ] Configure `GITHUB_TOKEN` with minimum required scopes
- [ ] Set `TIMELINE_REPO_URL` for your repository
- [ ] Set `.env` file permissions to 600: `chmod 600 .env`
- [ ] Verify `.env` is in `.gitignore` (already configured)
- [ ] Remove or override all default 'test' / 'test-key' values via environment variables
- [ ] Use absolute paths for all directory configurations
- [ ] Configure firewall rules to restrict API access
- [ ] Enable HTTPS/TLS for production deployments
- [ ] Review and rotate keys regularly

## API Authentication

### Current Implementation

The Research Monitor API uses header-based authentication:

```python
headers = {'X-API-Key': your_api_key}
```

### Security Notes

1. **API Key Storage**: Never log API keys or include them in error messages
2. **API Key Rotation**: Implement regular key rotation (recommended: every 90 days)
3. **API Key Validation**: Keys should be minimum 32 characters, random, unpredictable
4. **Rate Limiting**: Consider implementing rate limiting for production (not currently implemented)
5. **HTTPS Only**: Always use HTTPS in production to protect API keys in transit

## Database Security

### Current Configuration

- **Development**: SQLite database at `../unified_research.db`
- **Permissions**: Ensure database file is not world-readable

### Production Recommendations

1. Set restrictive file permissions:
   ```bash
   chmod 600 unified_research.db
   ```

2. Regular backups with encryption:
   ```bash
   # Example backup script
   sqlite3 unified_research.db ".backup '/secure/backup/location/backup-$(date +%Y%m%d).db'"
   chmod 600 /secure/backup/location/backup-*.db
   ```

3. Consider migrating to PostgreSQL for multi-user production deployments

## GitHub Token Security

### Required Scopes

The `GITHUB_TOKEN` requires **only** the following scope:
- `repo` - For creating pull requests and accessing repository

### Best Practices

1. Create token at: https://github.com/settings/tokens
2. Use **fine-grained tokens** (recommended) with repository-specific access
3. Set token expiration (recommended: 90 days)
4. Never commit tokens to version control
5. Rotate tokens before expiration
6. Revoke compromised tokens immediately

### Token Validation

On server startup, verify token has required permissions:
```bash
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

## Network Security

### Firewall Configuration

For production deployments:

1. Restrict access to Research Monitor port (default: 5558):
   ```bash
   # Example: UFW firewall
   sudo ufw allow from trusted_ip to any port 5558
   ```

2. Use reverse proxy (nginx/Apache) with HTTPS:
   ```nginx
   server {
       listen 443 ssl;
       server_name research.example.com;

       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;

       location / {
           proxy_pass http://127.0.0.1:5558;
           proxy_set_header X-API-Key $http_x_api_key;
       }
   }
   ```

## File System Security

### Directory Permissions

Set restrictive permissions on data directories:

```bash
chmod 700 timeline_data/
chmod 700 research_priorities/
chmod 700 timeline_data/validation_logs/
```

### Sensitive Data

The following paths may contain sensitive research data:
- `timeline_data/events/` - Timeline event data
- `research_priorities/` - Research task information
- `timeline_data/validation_logs/` - Validation history
- `unified_research.db` - Complete database

Ensure appropriate access controls and backup encryption.

## Logging and Monitoring

### Security Logging

**Do NOT log**:
- API keys (even partial values)
- GitHub tokens
- Secret keys
- User credentials

**DO log**:
- Failed authentication attempts
- API endpoint access patterns
- Validation failures
- File system errors

### Log Rotation

Implement log rotation to prevent disk space exhaustion:

```bash
# Example logrotate configuration
/var/log/research-monitor/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 research-monitor research-monitor
}
```

## Incident Response

### If Credentials Are Compromised

1. **Immediately** revoke compromised credentials:
   - Regenerate `RESEARCH_MONITOR_API_KEY`
   - Regenerate `RESEARCH_MONITOR_SECRET`
   - Revoke GitHub token at https://github.com/settings/tokens

2. Update `.env` with new credentials

3. Restart Research Monitor server:
   ```bash
   python3 research_cli.py server-restart
   ```

4. Review access logs for suspicious activity

5. Notify all authorized users of credential rotation

### Security Issue Reporting

To report security vulnerabilities:
1. **DO NOT** create public GitHub issues
2. Contact project maintainers privately
3. Include detailed reproduction steps
4. Allow reasonable time for fix before public disclosure

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GitHub Token Best Practices](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [SQLite Security Best Practices](https://www.sqlite.org/security.html)

---

**Last Updated**: 2025-10-16
**Next Review**: 2025-11-16 (monthly security review recommended)
