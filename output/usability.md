# Campus Customs usability improvements

## 1. Chat typing indicator

The floating chat now shows “Typing...” with three animated pink dots while its request is pending. It starts when the shopper sends a message and stops on either success or failure. Send/input controls remain disabled while waiting to avoid duplicate requests. The indicator uses `role="status"`, accessible text, and a reduced-motion CSS alternative. It replaces the earlier plain “Thinking…” message.

This reassures shoppers that the assistant received their request and reduces repeat submissions. The indicator represents a pending request, not token streaming.

## 2. Out of Stock product-card badges

The catalogue API and chat card hydration now include nullable `total_stock`, calculated with SQLite `SUM(quantity)` over all inventory sizes for that product. The shared React `Card` renders a high-contrast pink “Out of Stock” badge over the image only when `total_stock === 0`. Home, Products, and chat recommendation cards use the same component, retain their detail-page links, and use the same rule. Saved chat cards have stock totals refreshed when history loads.

A missing inventory record returns null and is not falsely labeled zero. A single sold-out size does not mark the entire product unavailable if another size has stock. Existing detail pages still show individual size quantities. Stock is a snapshot at load time; refresh/requery to see later changes.

Shoppers can spot unavailable products without opening every detail page, while the business avoids implying that an item is sold out merely because one size is unavailable. The test suite exercises an all-zero item and an unknown-inventory item in a temporary database; no real inventory was modified to manufacture a badge.

## 3. Related and complementary product suggestions

Registered `suggest_related_products(product_id, limit=4)` as the fourth agent tool. It reads real catalogue records, excludes the source product, and only considers candidates with positive total stock. It ranks candidates deterministically using shared search tags (three points each, ignoring generic “Yale” and “Campus Customs” tags) and matching garment type (two points). Different garment types with shared tags can serve as complementary suggestions. Ties use product name; at most six items can be requested.

`RelatedProducts` returns `status`, `source_product_id`, and `items`. Each `RelatedItem` contains a typed `ProductInfo` and a catalogue-based `reason`. Missing source products and no matches have explicit statuses. Returned IDs join this run's observed-product set, allowing the agent to select them for the existing clickable product cards. The prompt calls for this tool for alternatives, related items, or “what goes with this?” and requires separate size-stock checks when relevant.

This helps shoppers discover alternatives and coordinated campus apparel, increasing product discovery without inventing products, prices, bundles, or availability. Recommendations describe catalogue similarity, not a stylist's guarantee or personalized purchase-history ranking.

## 4. Bounded agent history

Added `backend/context.py` and applied `truncate_history()` immediately before converting history into PydanticAI messages. Both signed-in and guest requests now share the same final limits: at most 12 historical messages and at most 8,000 historical text characters. The function retains the most recent complete user/assistant exchanges in chronological order and stops when the next older pair would exceed either budget. Orphan messages are omitted; message text is never cut mid-sentence. The current request (separately limited to 2,000 characters), system instructions, and customer/page dependencies are not removed.

The earlier implementation limited message count only. A character budget additionally prevents long replies from filling the input context. This is a predictable text-size budget, not an exact tokenizer-based cap on total model tokens; tool responses, instructions, and reasoning also use tokens. Existing limits of eight model requests and 4,000 completion tokens per model request remain in place.

Database history is not deleted or summarized. Signed-in users can still reload up to 50 saved turns in the UI even though only recent bounded context goes to the model. The prompt instructs the agent to ask for clarification if an older detail is no longer available. This reduces repeated input costs and latency while preserving recent conversational continuity.

## Verification

- Frontend TypeScript check and production build passed.
- Nine backend tests passed across authentication, chat, tools, memory, and usability.
- Temporary-database tests verify zero vs unknown stock, exclusion of sold-out/source products from recommendations, real prices, and missing-product behavior.
- History tests verify the character limit, message limit, chronological recent-pair retention, and orphan removal.

Run from `HW 4`: `.venv/bin/python -m unittest backend.test_auth backend.test_chat backend.test_tools backend.test_memory backend.test_usability`. Run `npm run build` from `HW 4/frontend`.
