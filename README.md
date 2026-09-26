# Campus Customs — homework submission

A Yale Blue storefront built with React, Vite, and TypeScript, plus FastAPI, SQLite, and a PydanticAI shopping assistant. Features include searchable products, detail pages, secure account sessions, database-backed chat tools, product cards, customer memory, related recommendations, and an append-only audit trail.

## Requirements

- macOS or Linux (audit file locking uses POSIX `fcntl`).
- Python 3.11+ and Node.js 22+ with npm.
- The course data pack, provided separately.
- Your own funded OpenAI API key for live AI chat. ChatGPT/Codex subscriptions do not supply API credits. The store and authentication work without a key; chat returns a configuration error until configured.

## Repository layout

```text
.
├── .env.example
├── .gitignore
├── README.md
├── AI_prompts.md
├── backend/
│   ├── main.py
│   ├── agent.py
│   ├── tools.py
│   ├── models.py
│   ├── auth.py
│   ├── memory.py
│   ├── context.py
│   ├── audit.py
│   ├── requirements.txt
│   ├── prompts/prompt.md
│   └── test_*.py
├── frontend/
│   ├── package.json
│   ├── package-lock.json
│   ├── index.html
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.tsx
│       └── style.css
├── output/
│   ├── harness.md
│   ├── usability.md
│   ├── design.md
│   ├── audit_trail.json
│   ├── app_check.html
│   └── app_check_images/
└── data/                  # supplied locally; database/images are ignored
    ├── campus_customs.db
    └── products/*.jpg
```

Use this directory (`HW 4` in the original workspace) as the repository root, not the parent containing other homework. `.env`, `.venv`, data.zip, database files, product images, node_modules, and dist are local-only and excluded from Git.

## 1. Place the course data pack

From the repository root, extract the supplied archive here if it already contains a `data/` folder:

```sh
unzip /path/to/data.zip -d .
```

Or manually place `campus_customs.db` in `data/` and the images in `data/products/`. Do not create `data/data/`. The database must contain `catalogue`, `inventory`, and `users`. It must be writable for registration, sessions, and chat memory; the backend initializes the additional tables on startup. Catalogue tools themselves use read-only connections. Do not replace a database containing accounts you want to retain.

## 2. Configure local environment

```sh
cp .env.example .env
```

Edit `.env` and replace `YOUR_OPENAI_API_KEY_HERE` with your own key. Do not commit it. The default model is `gpt-5-mini`; `CAMPUS_CHAT_MODEL` changes it, but other models may need compatible reasoning settings. For HTTP development leave `COOKIE_SECURE=false`.

The application loads the repository-root `.env` using an absolute path. Exported environment variables take precedence; an original-workspace parent `.env` is only a fallback for values not already set. Restart the backend after editing environment values or the Markdown prompt.

## 3. Start FastAPI

From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
cd backend
source ../.venv/bin/activate
uvicorn main:app --reload --port 8000
```

API documentation: http://127.0.0.1:8000/docs

## 4. Start React in a second terminal

From the repository root:

```sh
cd frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open http://127.0.0.1:5173/. Vite proxies `/api` and `/images` to port 8000; use the same hostname throughout for cookie sessions. If Vite chooses another port, stop the conflicting server or update `FRONTEND_ORIGINS` when using direct cross-origin requests.

## Grader walkthrough

1. Browse Products and click a card to view its image, description, price, colors, and size inventory.
2. Sign in with the course seed account `test@campuscustoms.yale.edu` / `password`, or create an account with a 12–128 character password. The seed credential is intentionally public test data; never use it for a public production shop.
3. Ask “What hoodies do you have?” to display matching clickable cards.
4. Ask for the price and XS stock of Baseball Left Chest Crewneck; compare with the supplied database.
5. On a product detail page, ask “Do you have this in pink?” or request related products.
6. Refresh while logged in to restore saved chat. Guest history is not persisted.
7. Inspect `output/audit_trail.json`: it is JSON Lines (one JSON object per line), appended to across runs and never reset by the app. It intentionally remains in the submission as activity evidence, with redacted summaries rather than chat transcripts.

Out-of-stock badges appear only when the total over all recorded sizes is zero. The supplied data may have no completely sold-out product; tests verify the badge data using a temporary database instead of altering the course data.

## Tests and build

From the repository root:

```sh
.venv/bin/python -m unittest backend.test_auth backend.test_chat backend.test_tools backend.test_memory backend.test_usability backend.test_audit
cd frontend
npm run build
```

Tests need the local data pack. Offline tests do not call the live model. Some agent tests append audit events; the preservation test uses a temporary audit file. A live chat uses your API balance.

## Documentation and boundaries

- `output/harness.md`: models, tools, API contracts, authentication, memory, audit format, safety rules, and limits.
- `output/usability.md` and `output/design.md`: implemented usability and visual choices.
- `output/app_check.html`: three attached screenshots in `output/app_check_images/`; review their captions and personal information before final submission.
- `AI_prompts.md`: recorded assignment prompts.

This is a local homework storefront, not a checkout system. Payments, order tracking, email verification, password reset, and MFA are not implemented. Production needs HTTPS (`COOKIE_SECURE=true`), protected database/backups, shared rate limiting, and a production reverse proxy with SPA routing. The repository ignores local credentials and data; screenshots should also be reviewed for personal information before publication.
