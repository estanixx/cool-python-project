# Website — Next.js SSR Frontend

Next.js 14 App Router application with shadcn/ui components, deployed to AWS Amplify (WEB_COMPUTE / SSR).

## Pages

| Route | Domain | Description |
|-------|--------|-------------|
| `/` | Home | Navigation to all tools |
| `/dictionary` | Dictionary | Add, list, and lookup word definitions |
| `/shopping` | Shopping | Browse products, manage cart |
| `/word-trick` | Word Trick | Apply word-trick algorithm to sentences |

## Architecture

```
Browser ──► Next.js (Amplify SSR)
               │
               ├── Server Components ──► API Gateway ──► Lambda ──► DynamoDB
               │
               └── Client Components ──► API Gateway (CORS) ──► Lambda
```

### API Communication

The frontend uses a centralized API client (`lib/api-client.ts`) that unwraps API Gateway v2 response envelopes:

- **Development**: Requests go through `/api/proxy/[...path]` (Next.js route handler) that invokes Lambdas directly via Floci's Lambda API, bypassing the broken API Gateway v2 in Floci v1.5.16.
- **Production**: Requests go directly to the API Gateway URL (set via `NEXT_PUBLIC_API_URL` env var). CORS is configured on the API Gateway to allow Amplify origins.

### API Proxy Route (Development Only)

`app/api/proxy/[...path]/route.ts` intercepts API calls in local dev and:

1. Extracts the Lambda function name from the URL path
2. Builds an API Gateway v2 event envelope (path params, query params, headers)
3. Invokes the Lambda directly via `POST /2015-03-31/functions/{name}/invocations`
4. Returns the Lambda's response wrapped in the standard envelope

## Development

```bash
# Full stack with docker-compose (Floci + Terraform + MCP + Website)
docker-compose up -d

# Or standalone
cd website
cp .env.example .env.local
npm install
npm run dev
```

The dev server is available at `http://localhost:3000`.

## Dependencies

- **Next.js 14** — App Router, Server Components, SSR
- **shadcn/ui** — Component library (Radix UI primitives + Tailwind)
- **Tailwind CSS** — Styling
- **TypeScript** — Type safety
- **Vitest** — Unit testing

## Project Structure

```
website/
├── app/                    # Next.js App Router pages
│   ├── api/proxy/          # Lambda proxy route (dev only)
│   ├── dictionary/         # Dictionary page
│   ├── shopping/           # Shopping / Cart page
│   └── word-trick/         # Word Trick page
├── components/             # Client components
│   ├── ui/                 # shadcn/ui primitives
│   ├── dictionary-client.tsx
│   ├── shopping-client.tsx
│   ├── cart-modal.tsx
│   └── word-trick-client.tsx
├── lib/                    # Utilities
│   ├── api-client.ts       # Centralized API client
│   └── utils.ts            # cn() helper
├── types/                  # TypeScript types
│   └── api.ts              # API response types
└── public/                 # Static assets (if any)
```

## Deployment

The site is auto-deployed to Amplify on push to the connected branch. Build spec is at `amplify.yml` (repo root) with `appRoot: website`.

### Amplify Domain Outputs

After `terraform apply` in `infra/prod`, the website domain is available as outputs:

```bash
# Amplify app ID
terraform -chdir=infra/prod output amplify_app_id

# Default domain (e.g., d1234567890.amplifyapp.com)
terraform -chdir=infra/prod output amplify_default_domain

# Constructed URL for main branch
terraform -chdir=infra/prod output amplify_branch_url
```

The CD workflow also prints the Amplify default domain in the deploy job logs after a successful apply.

Environment variables for production are set via Terraform (`infra/prod/amplify.tf`):

| Variable | Source | Description |
|----------|--------|-------------|
| `NEXT_PUBLIC_API_URL` | `module.crud.api_endpoint` | API Gateway invoke URL |
| `NODE_ENV` | hardcoded | `production` |
