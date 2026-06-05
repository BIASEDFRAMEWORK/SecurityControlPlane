## Summary

Moves the payment provider token lookup into environment-driven configuration.

## Security intent

### Does this change touch secrets, credentials, tokens, environment variables, or sensitive configuration?

- [x] Yes - this change touches secrets, credentials, tokens, environment variables, or sensitive configuration
- [ ] No - this change does not touch secrets, credentials, tokens, environment variables, or sensitive configuration

### Areas touched

- [ ] Secrets, credentials, tokens, or keys
- [x] Environment variables
- [x] Sensitive configuration
- [ ] None of the above

### Explanation

The change reads the payment provider token from `PAYMENT_PROVIDER_TOKEN` at runtime instead of storing it in source control.

### Safety validation / evidence

Ran the app locally with and without `PAYMENT_PROVIDER_TOKEN`; the app reports the token source without printing the token value.
