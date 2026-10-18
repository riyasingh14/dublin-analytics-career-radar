# Vercel deployment — React website and Python analytical API

## Deployment shape

The public website is a React/Vite build, served as static assets by Vercel. The four
tools call the same-site Flask function at `/api/index`, which reuses the tested
Python analytical core. The function is stateless: it does not run Streamlit, keep
candidate sessions, read private snapshots, schedule collection or invoke an
external model. Streamlit remains available as an internal research workbench.

`vercel.json` configures Vite, `dist`, a 30-second function ceiling, the source/taxonomy
files needed by the Python function, and response headers. Production Node target
is 22.x. The Python code supports 3.12; use a supported Vercel Python runtime.

Root `requirements.txt` contains only Flask and its small dependencies. The local
research/test stack is in `requirements-local.txt` (which includes the deployment
requirements). This avoids bundling Streamlit, pandas, PyArrow and Plotly into the
Python function. `package-lock.json` pins the frontend dependency resolution.

The API has a 64 KB request limit, 30,000-character description limit,
500-character evidence-note limit, validated requirement IDs/classifications and
bounded synthetic scenarios (at most 1,000 people over eight years). It returns
safe errors, does not log request bodies, and marks responses `no-store`. Hosting
providers may retain operational request metadata under their own policies.

## Public data mode

The deployment always uses an explicitly generated Skill Constellation fixture and
synthetic mobility histories. It has no environment-variable switch to expose the
private 32-job development dataset. No API token or secret is needed for this demo.

The private data directories and research interface are excluded from Vercel uploads.
Source/display permission, human evaluation and a deliberate public-data pipeline
remain prerequisites for releasing observed vacancies. Do not remove these boundaries
merely to fill the public site with real records.

Candidate evidence and pasted descriptions are sent transiently to this site's API
when analysis is requested. They are not stored by the application or sent to a
third-party LLM. Tool reset removes browser state; downloads already saved remain
on the user's device. No real callback or salary prediction is provided.

## Local setup

```bash
cd /workspace/dublin-analytics-career-radar
python -m venv .venv
.venv/bin/python -m pip install -r requirements-local.txt
npm ci
```

Run the backend in one terminal:

```bash
.venv/bin/python api/index.py
```

Run the frontend in a second terminal:

```bash
npm run dev
```

Vite proxies `/api` to the local backend. The frontend uses hash routes, so nested
tool URLs work without a catch-all rewrite that could accidentally mask API errors.

## Validation

```bash
npm run build
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
npx playwright install chromium
npm test
```

When the machine already has Chromium, set
`PLAYWRIGHT_CHROMIUM_EXECUTABLE=/usr/bin/chromium` for `npm test` instead of downloading
a browser. `CAREER_RADAR_PYTHON` can override the test server Python executable;
its default is `.venv/bin/python`. Playwright starts the local services if needed.

The production frontend build, Python boundary tests, a deployment-only virtual
environment and full browser flows are local validation. They do not prove that a
Vercel account is linked or a hosted deployment has succeeded. Hosted smoke checks
must be repeated after the deployment returns an actual URL.

## Connect through GitHub — recommended

1. Sign in at <https://vercel.com/new> using your own account/team.
2. Connect GitHub and grant access to `riyasingh14/dublin-analytics-career-radar`.
3. Import that repository and choose `main` as the production branch.
4. Keep **Root Directory at the repository root**. Do not select `web`, `api` or `src`.
5. Framework preset: **Vite**. The committed config supplies build command
   `npm run build` and output directory `dist`.
6. No Adzuna, Apify or other secret is needed for the public demo. Leave those keys
   out of the project unless a later explicitly approved server-side collection
   workflow requires them.
7. Deploy. Inspect the build/function logs if the deployment fails; do not treat a
   successful Git push as a successful deployment.

The account owner must perform the Vercel/GitHub authorisation step if no connected
Vercel session is available to the coding environment. Do not paste tokens into chat
or commit `.vercel` files. A Vercel project link or deployment URL can be shared for
read-only verification; token-bearing URLs should not be shared.

GitHub integration can deploy subsequent `main` commits automatically and create
previews for branches/PRs. Keep an eye on the Vercel plan's function/runtime quotas.
No recurring paid plan or collection spending is required by this implementation.

## Hosted smoke checks

After an actual deployment, confirm:

- Home loads its styles and tool cards on desktop and mobile.
- `/api/index?action=health` returns `status: ok` and `data_mode: synthetic-demo`.
- Bootstrap reports 30 fictional postings; no private source records appear.
- Constellation's rest-of-Ireland view becomes a sparse 10-posting sample.
- Diagnostic analysis works, and Clear removes the report.
- Readiness needs evidence notes, supports hypothetical comparison and clears inputs.
- Mobility generates labelled histories, filters cohorts and suppresses sparse salary
  comparisons. No public output implies observed salary returns.
- Each `#/tool` route opens directly and downloads work.

Roll back through Vercel's deployment controls if any material hosted check fails.
Keep the last known-good release and inspect the underlying error before retrying.

## Current connection status

The owner reports deployment at
<https://dublin-analytics-career-radar.vercel.app/> and previously confirmed GitHub
is connected. This workspace has no linked Vercel project or authenticated CLI
session. Requests to the supplied URL fail at the egress proxy with tunnel HTTP
403; direct Playwright requests fail DNS resolution (`EAI_AGAIN`). Neither result
establishes an application failure or a successful hosted release.

The requested official `vercel/vercel-plugin` was downloaded and installed with
`plugins@1.3.5`. Its standard Codex marketplace install failed because neither
configured curated marketplace contained `vercel`; installing the same official
repository through the installer's supported local-source mode succeeded. It
updated the user-level plugin cache, marketplace and Codex configuration outside
this repository. The installer explicitly requires an agent-tool restart. No
Vercel MCP tools or Vercel OAuth grant are active in this conversation yet.
Installation is not account authentication.

After restarting/loading the plugin, complete its Vercel OAuth flow. Verify the
account/team and existing project's Git repository before linking or deploying.
The existing GitHub integration can deliver subsequent `main` commits without a
workspace token; its production branch and resulting deployment status still need
account-side verification. Do not paste access tokens into chat. If the workspace
uses an Internet allowlist, retain existing destinations and allow the supplied
deployment hostname, `mcp.vercel.com`, `api.vercel.com`, `vercel.com` and any actual
OAuth redirect destination reported by the supported login flow.

## Repeatable release verification

```bash
npm run test:deployed -- https://dublin-analytics-career-radar.vercel.app/
# Smaller API-only check:
npm run test:deployed -- https://dublin-analytics-career-radar.vercel.app/ --grep 'release API'
```

This requires Playwright Chromium (or `PLAYWRIGHT_CHROMIUM_EXECUTABLE`). The runner
requires an explicit HTTPS origin without credentials, path, query or fragment.
It sets the suite's remote base URL and disables both local test servers. Failures
retain their exit status. The tests use synthetic inputs and make no paid source
calls. They cover all four tools, mobile navigation, downloads, API health,
synthetic-only bootstrap, filtered denominators and safe validation errors.

`.github/workflows/quality.yml` runs the build, Python suite and local browser/API
suite on pushes to `main` and pull requests. `.github/workflows/hosted.yml` runs the
same browser/API suite on successful production `deployment_status` events and
supports manual **Run workflow** with a deployment URL. The deployment-event path
checks out the deployed commit to avoid testing future UI expectations against an
older release. Automatic execution depends on Vercel emitting GitHub deployment
events; use the manual workflow if it does not. Protected preview URLs may require
authenticated Vercel access; do not disable protection to make tests pass.

The workflows are configured but their hosted GitHub execution has not been
observed from this workspace. Inspect the Actions results and Vercel deployment
logs after pushing. Local green checks alone are not hosted acceptance evidence.
