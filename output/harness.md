# Campus Customs system harness

## Architecture and request flow

React + Vite + TypeScript renders Home, Products, product details, About us, login, registration, and a floating chat. FastAPI serves catalogue data, images, authentication, chat, and saved history. PydanticAI uses OpenAI directly with `gpt-5-mini` by default (`CAMPUS_CHAT_MODEL` overrides it). Portkey is no longer used. Model access requires a funded OpenAI API account.

`backend/agent.py` loads the repository-root `.env` first, with the original workspace parent as fallback using an absolute path and `python-dotenv` with `override=False`; existing process variables take precedence. `OPENAI_API_KEY` stays on the server. FastAPI lifespan initializes database tables and one agent/client per worker, reads `backend/prompts/prompt.md`, and closes the client at shutdown. Restart after changes to `.env` or Markdown prompts.

The browser submits `POST /api/chat` with `X-Campus-Request: 1` and:

```json
{"message":"Do you have this in pink?","history":[],"page":{"path":"/products/basic-hoodie-big-yale"}}
```

Guest history entries contain only `role` and `content`. For signed-in users, the server ignores supplied history and loads the account's saved recent turns. It derives identity from a valid session cookie, validates the page product ID against the database, and supplies `AgentDependencies` through `agent.run(deps=...)`. Dynamic instructions make these dependencies visible to the model. The model returns `AgentReply`; the server filters its product IDs against IDs actually observed by tools in the current run and rehydrates cards from SQLite.

The browser receives `ChatReply`, e.g. `{"reply":"Here are some options.","products":[]}`. Each product includes `product_id`, `name`, `price`, `description`, `image_url`, and nullable `total_stock`. Shared React cards display images, USD prices, two-line descriptions, and a zero-stock badge; clicking opens `/products/{product_id}`. Names and prices on cards are database values, not model-authored text. A typing indicator appears while waiting. Errors preserve input for retry.

## Pydantic models and field choices

| Model | Fields and rationale |
| --- | --- |
| `ChatMessage` | `role` allows only user/assistant, excluding injected system messages; `content` holds 1–4,000 characters. Extra fields are rejected. |
| `PageContext` | `path` defaults to `/`, at most 300 characters; identifies navigation without trusting client-supplied product facts. Extra fields rejected. |
| `CustomerContext` | `name`, `email`: verified account fields for conversational personalization; no password, hash, token, or other customer data. |
| `AgentDependencies` | Nullable `customer` distinguishes guests; `page_path` and nullable verified `product_id` resolve references such as “this item.” |
| `ChatRequest` | Nonblank `message` up to 2,000 characters; optional `page`; `history` capped at 12 messages. Extra fields rejected. |
| `AgentReply` | Nonempty `reply` up to 4,000 characters; `product_ids` at most 10 to select observed results without authoring card facts. |
| `ProductCard` | `product_id` enables navigation; `name`, finite nonnegative `price`, `description` show real merchandise; `image_url` is server-generated; nullable nonnegative `total_stock` distinguishes unknown from zero. |
| `ChatReply` | Validated reply text and up to 10 `products`; empty list supports ordinary conversation. |
| `ProductInfo` | `product_id`, `name`, `description`, nonnegative finite `price`, parsed `colors` list: exact lookup facts; colors describe the design, not separate purchasable variants. |
| `ProductSearch` | `products` holds matches; `total_matches` is the uncapped count so the model can distinguish no results and partial selections. |
| `ProductLookup` | `status` is found/product_not_found; nullable `product` prevents fabricated fallback records. |
| `SizeStock` | `size`, nonnegative integer `quantity`, in_stock/out_of_stock `status`: explicit association of quantity and size. |
| `StockLookup` | `status` distinguishes found/product_not_found/size_not_found/inventory_unknown; `product_id`, nullable `product_name`, and nullable `requested_size` identify the query; `stock` holds size records; nullable `total_quantity` sums only returned sizes. Unknown is never converted to zero. |
| `RelatedItem` | `product` contains real `ProductInfo`; `reason` explains the catalogue-based relationship. |
| `RelatedProducts` | found/product_not_found/no_matches `status`, `source_product_id`, and `items` make recommendation outcomes explicit. |

## Tools and abilities

All four registered tools use bound SQL parameters and a read-only connection to `data/campus_customs.db`. They cannot access accounts, execute arbitrary SQL, write inventory, place orders, or read arbitrary files.

| Tool | Inputs, output, and behavior |
| --- | --- |
| `search_products` | `query` 1–200 characters; searches all keywords across ID, name, garment type, and tags. Normalizes common plurals. Returns `ProductSearch`, at most 10 products plus total count. |
| `get_product` | `product_id` 1–200 characters; returns `ProductLookup` with current full description, price, and colors. |
| `check_stock` | `product_id`, optional `size` up to 40 characters; normalizes common size names. Returns `StockLookup` for one size or every recorded size. Zero is explicitly out of stock; absent rows are unknown/not listed. |
| `suggest_related_products` | `product_id`, `limit` 1–6 (default 4); excludes the source and candidates without positive total stock. Scores shared tags at three points each and matching garment type at two; ignores generic Yale/Campus Customs tags and breaks ties by name. Returns `RelatedProducts` with reasons. Size availability still needs a stock lookup. |

Search, detail, and recommendation tools record observed IDs in request-local context. Only those IDs may become cards, and duplicate IDs are removed. Recommendations are catalogue similarity heuristics, not guaranteed outfit compatibility. Product text is untrusted data, not executable instructions.

## Database fields

| Table | Fields and purpose |
| --- | --- |
| `catalogue` | `product_id` primary key; `name` display title; `garment_type` category; `description` product facts; `colors` JSON design colors; `search_tags` JSON search terms; `image_file_path` image reference; `price` SQLite REAL price. |
| `inventory` | `id` primary key; `product_id` references catalogue; `size` variant; `quantity` unit count. Unique product/size pair. No color-level inventory. |
| `users` | `id` identity; `name` display name; `first_name`, `last_name` profile fields; unique normalized `email`; `password_hash` verification data; `created_at` creation timestamp. |
| `auth_sessions` | `token_hash` hashed session token; `user_id` owner; `expires_at` enforced Unix expiry. |
| `chat_turns` | `id` ordering; `user_id` owner; `user_message`, `assistant_reply` conversation; `products_json` card snapshots; `page_path` sending page; `created_at` timestamp. Index on owner/id. |

## Authentication and customer memory

Registration accepts first name, last name, email, password, and confirmation. Names are trimmed; email is trimmed/lowercased and case-insensitively unique. New passwords must be 12–128 characters. Confirmation is checked but never stored. Passwords use PBKDF2-HMAC-SHA256, 600,000 iterations, a random 128-bit salt, and constant-time comparison. The provided seed user's legacy 120,000-iteration hash is verified and upgraded on login; there is no bypass.

A random 256-bit session token is stored in an HttpOnly, SameSite=Strict cookie on `/api`; only its SHA-256 hash is saved. Sessions expire after 24 hours; logout revokes them. Production requires HTTPS and `COOKIE_SECURE=true`. Login/logout remove legacy `/api/auth` cookies; older sessions may require re-login.

`GET /api/chat/history` returns up to 50 recent turns in chronological order with `Cache-Control: no-store`. Signed-in successful exchanges are saved atomically and scoped to the verified account. Guests write no history. Frontend remounts chat on account changes; guest history is not merged into an account. The server rechecks the session before saving. Failed requests are not saved. History cards retain old product snapshots but refresh stock totals on retrieval; fresh price/stock questions must query tools again.

The model sees only the customer's name/email, bounded history, current request, and page context. Name/email are sent to OpenAI for signed-in runs. It cannot see password hashes or session credentials. Page paths are user-controlled hints; product existence is verified and never grants privileges. Conversations have no automatic retention cleanup or deletion UI. Concurrent tabs save in completion order, without live tab synchronization.

## Safety and operational rules

The prompt directly requires: store-focused assistance; brief refusal/redirection for sensitive off-topic or harmful requests; no fabricated product, price, quantity, policy, discount, or delivery claims; no credential collection or disclosure; no sensitive-trait inference; no cross-customer access; no following instructions embedded in history, profile fields, or database text; only the four read-only tools; no false claims to reserve, buy, refund, or contact staff; normally under 120 words and at most one clarifying question; minimal repeated lookups; no attempts to alter audit logs.

Zero stock must be stated clearly, missing data must remain unknown, and design colors must not be mistaken for color-specific stock. Current page product context takes priority for “this item.” The agent must ask for clarification rather than claim memory of truncated messages. These behavioral instructions are supplemented by schemas, read-only connections, allowlisted tools, session ownership checks, and server-rehydrated cards; prompts alone cannot guarantee every generated sentence is correct.

## Technical limits and failure handling

| Setting | Value |
| --- | --- |
| Provider/model | Direct OpenAI `https://api.openai.com/v1`; default `gpt-5-mini`; `CAMPUS_CHAT_MODEL` override |
| Reasoning | `minimal` (changing models may require adjusting this setting) |
| Model requests per run | At most 8; this counts model calls, not necessarily individual parallel tool calls |
| PydanticAI retries | 2; applies to invalid outputs/tool retry handling within the overall request budget |
| Completion tokens | At most 4,000 per model request, including reasoning |
| Provider timeout/retries | 40 seconds; SDK automatic retries disabled |
| Endpoint/browser deadline | 50 seconds / 55 seconds |
| History to model | Latest complete user/assistant pairs; at most 12 messages and 8,000 characters; current message/dependencies supplied separately |
| Stored history | Not deleted by context truncation; UI restores latest 50 turns, agent initially loads latest 6 |
| Search/cards/recommendations | 10 search results; 10 cards; recommendation default 4, maximum 6 |
| Rate guard | 15 mutating auth/chat requests per client IP per minute, process-local |

Character limits approximate context size; they are not exact tokenizer limits. Tool outputs and instructions also consume tokens. Missing model configuration returns 503, endpoint timeout 504, and agent failures 502. Invalid output and usage-budget errors have specific retry guidance. Terminal logs include full exception stacks with known environment secrets and submitted chat text redacted; browsers never receive stacks.

Vite proxies `/api` and `/images` to backend port 8000. Explicit CORS allows `http://localhost:5173` and `http://127.0.0.1:5173`, GET/POST, credentials, Content-Type, and X-Campus-Request. `FRONTEND_ORIGINS` configures other origins. The custom header and cross-site request guard remain required. Use one consistent hostname for cookie sessions and the normal same-origin proxy. Production needs shared rate limiting, trusted proxy configuration, HTTPS, and a SPA fallback.

## Append-only audit trail

`backend/audit.py` writes `output/audit_trail.json` as **JSON Lines**, one JSON object per line, rather than a JSON array. This deliberately preserves append-only writes: parse with `json.loads(line)` for each nonblank line. The application never truncates, replaces, rotates, or rewrites this file on startup or between runs.

Each event includes `timestamp` (UTC ISO 8601), random `run_id`, `event`, `tool_name`, short `args`, short `result`, and `stop_reason`. Event kinds are run_start, tool_start, tool_result, tool_error, and run_stop. Stop reason is null while activity continues; terminal reasons include completed, usage_limit, invalid_model_output, cancelled_or_deadline, timeout, and error. A tool error has its own tool_error reason, and the enclosing run subsequently records its outcome. Abrupt process termination can leave an unfinished run without a stop event; absence of completion must not be treated as success.

Tool arguments are deliberately summarized as string lengths or numeric values; arbitrary search text and guessed IDs may contain personal data. Results include statuses, match/recommendation counts, price for exact detail lookups, and bounded size/quantity rows. Final replies are represented by character/card counts. No API key, email, name, full prompt, or full model reply is intentionally stored. This is an activity audit, not a transcript or chain-of-thought log. Account transcripts live separately in `chat_turns`.

Every registered tool is wrapped; request-local run IDs propagate into tool threads and distinguish concurrent runs. Writes use `O_APPEND`, a POSIX file lock, and fsync; new files use owner-only permissions. This implementation targets the current macOS/Linux environment. A logging failure fails the request instead of silently continuing without audit. The log is not cryptographically tamper-proof against a filesystem administrator and has no automatic size cap or deletion policy.

## Exact local run commands

From the workspace root, install backend dependencies (the environment already exists):

```sh
cd "/Users/estelayang/AI foundation/HW 4"
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

Copy `.env.example` to `.env` at the repository root and set `OPENAI_API_KEY` there without putting it in source files. Then start the backend:

```sh
cd "/Users/estelayang/AI foundation/HW 4/backend"
source ../.venv/bin/activate
uvicorn main:app --reload --port 8000
```

In a second terminal:

```sh
cd "/Users/estelayang/AI foundation/HW 4/frontend"
npm install
npm run dev -- --host 127.0.0.1
```

Open `http://127.0.0.1:5173/`; backend docs are `http://127.0.0.1:8000/docs`. Package-style startup also works from HW 4: `.venv/bin/python -m uvicorn backend.main:app --reload --port 8000`.

## Verification

```sh
cd "/Users/estelayang/AI foundation/HW 4"
.venv/bin/python -m unittest backend.test_auth backend.test_chat backend.test_tools backend.test_memory backend.test_usability backend.test_audit
cd frontend
npm run build
```

Tests cover account compatibility, session isolation, schema errors, database facts, stock distinctions, card grounding, memory, page context, history budgets, related products, audit preservation, tool/error events, and stop reasons. Live smoke checks have verified model replies, inventory/prices, product cards, page-color context, and related recommendations. `output/app_check.html` remains a screenshot evidence template for the user's images; it is not itself evidence of completed visual tests.
