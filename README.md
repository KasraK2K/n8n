# n8n Docker Stack

This stack gives you a production-leaning local n8n deployment with:

- PostgreSQL for durable storage
- Redis-backed queue mode
- A dedicated worker for executions
- One external task runner for worker-side Code node execution
- Health checks and restart policies
- A custom n8n image with a small set of shell tools
- A shared `/files` mount for workflows that need local file I/O

## Secure defaults

This repo now starts with safer defaults:

- `Execute Command` is disabled by default via `NODES_EXCLUDE`
- Code node built-ins are restricted (`NODE_FUNCTION_ALLOW_BUILTIN=crypto,path,util`)
- External npm imports in Code nodes are disabled (`NODE_FUNCTION_ALLOW_EXTERNAL=`)
- Extra runner npm packages are not preinstalled (`JS_EXTRA_PACKAGES=`)

## Included command-line tools

The custom n8n image installs:

- `bash`
- `curl`
- `jq`

Those commands are available inside the main and worker containers.

## Start the stack

```powershell
docker compose up -d --build
```

Then open:

- [http://localhost:5678](http://localhost:5678)

## Enable powerful features intentionally

If you trust your workflows and need more flexibility, edit `.env`.

Enable `Execute Command`:

```dotenv
NODES_EXCLUDE=[]
```

Allow more Node.js built-ins in Code node:

```dotenv
NODE_FUNCTION_ALLOW_BUILTIN=crypto,path,util,fs
```

Allow external npm packages in Code node:

```dotenv
JS_EXTRA_PACKAGES=axios dayjs zod
NODE_FUNCTION_ALLOW_EXTERNAL=axios,dayjs,zod
```

Apply changes:

```powershell
docker compose build
docker compose up -d
```

## Files written by workflows

Anything in `./workspace` on the host is mounted into n8n at `/files`.

This gives your workflows a safe, predictable place to read and write files without touching the rest of the container filesystem.

`workspace` runtime files are git-ignored, except `workspace/.gitkeep`.

## If you plan to expose this publicly

Before putting this on the internet, you should:

1. Put it behind a reverse proxy with TLS
2. Set `N8N_HOST`, `N8N_EDITOR_BASE_URL`, and `WEBHOOK_URL` to your real domain
3. Keep `NODES_EXCLUDE`, `NODE_FUNCTION_ALLOW_BUILTIN`, and `NODE_FUNCTION_ALLOW_EXTERNAL` as restrictive as possible
4. Rotate the generated secrets in `.env`
