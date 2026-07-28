# Git Provider

The Git provider supports local repositories, GitHub HTTPS URLs, and Bitbucket HTTPS URLs.

Accepted remote URL forms:

- GitHub repo URL: `https://github.com/acme/payments`
- GitHub clone URL: `https://github.com/acme/payments.git`
- GitHub browser URL: `https://github.com/acme/payments/tree/main/src`
- Bitbucket repo URL: `https://bitbucket.org/acme/payments`
- Bitbucket clone URL: `https://bitbucket.org/acme/payments.git`
- Bitbucket source URL: `https://bitbucket.org/acme/payments/src/master/`

Browser/source URLs are normalized to the repository clone URL. If the URL contains a branch segment, that branch is used unless `branch` is explicitly provided in the request.

## Remote Sync API

```http
POST /providers/git/sync
Content-Type: application/json

{
  "repo_url": "https://github.com/acme/payments",
  "access_token": "token-value",
  "branch": "main",
  "persist": true
}
```

For Bitbucket:

```json
{
  "repo_url": "https://bitbucket.org/acme/payments/src/master/",
  "access_token": "token-value",
  "branch": "main"
}
```

Optional fields:

- `platform`: `github` or `bitbucket`. Usually inferred from the URL.
- `username`: override the transport username. Defaults to `x-access-token` for GitHub and `x-token-auth` for Bitbucket.
- `branch`: clone or update a specific branch.
- `persist`: when `true`, generated episodes are written to Graphiti/FalkorDB. Defaults to `false`.

## Credential Handling

The provider normalizes repository URLs to HTTPS `.git` URLs and stores only the sanitized URL as the resource ID.

The access token is supplied to Git through `GIT_ASKPASS` for clone/fetch operations. It is not embedded in:

- resource IDs
- clone directory names
- UKO metadata
- API responses
- provider status

## Output

The route clones or fetches the repository into `GIT_DEFAULT_CLONE_PATH`, emits file and commit UKOs, runs them through the pipeline, and returns counts:

```json
{
  "provider": "git",
  "platform": "github",
  "repo_url": "https://github.com/acme/payments.git",
  "resource_id": "https://github.com/acme/payments.git",
  "uko_count": 42,
  "episode_count": 108,
  "persisted": true
}
```
