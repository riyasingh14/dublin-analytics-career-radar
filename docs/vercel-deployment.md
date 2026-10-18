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

The user confirmed GitHub is connected to Vercel. This coding workspace has no
linked Vercel project or authenticated CLI session. A CLI login was attempted but
failed with a network fetch error. This does not establish a problem with the
user's Vercel account. Import/open the repository in the Vercel dashboard and share
the resulting deployment URL for hosted verification. No hosted URL has been
confirmed during this task.
