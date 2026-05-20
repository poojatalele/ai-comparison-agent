# OnPoint — AI Price Agent

Paste any product link (or type a name) and the agent finds the lowest price
across every major Indian retailer, ranked cheapest-first, and shows the
**onpoints** you'd earn on OnPoint partner stores.

## Architecture

A **hexagonal (ports & adapters)** layout — three independent layers:

```
onpoint-demo/
├── backend/          # DOMAIN CORE — pure Python, no web framework
│   ├── pyproject.toml
│   └── pricecompare/
│       ├── config.py            # Settings (env-driven, immutable)
│       ├── models.py            # domain types: ProductQuery, Offer, ...
│       ├── errors.py            # ResolutionError, ProviderError
│       ├── service.py           # PriceComparisonService (orchestrator)
│       ├── resolvers/           # raw input  -> ProductQuery   (Strategy + Chain)
│       ├── providers/           # ProductQuery -> Offers       (SerpAPI / Mock / Fallback)
│       ├── rewards/             # OnPoint cashback rates        (live API + cache)
│       └── processing/          # Offers -> ranked Offers       (filter / rank / enrich)
├── server/           # HTTP LAYER — FastAPI adapter
│   ├── main.py                  # ASGI entry point
│   ├── app.py                   # application factory
│   ├── container.py             # composition root (wires the core)
│   ├── schemas.py               # API request/response models
│   └── routes/                  # /api/compare, /api/health, pages
└── frontend/         # STATIC UI
    ├── index.html
    ├── css/styles.css
    ├── js/app.js
    └── assets/                  # fonts, favicon
```

**Dependency direction:** `frontend → server → backend`. The backend depends on
nothing — it knows nothing about HTTP or FastAPI.

## Why it's structured this way (SOLID)

| Principle | Where |
|---|---|
| **Single Responsibility** | Each module does one thing — a resolver resolves, a provider fetches, a processor transforms. |
| **Open/Closed** | Add a new price source / resolver / processing step by writing one class and adding it to a list in `server/container.py`. No existing file changes. |
| **Liskov Substitution** | Every `PriceProvider` (real, mock, fallback) is interchangeable; the service can't tell them apart. |
| **Interface Segregation** | Tiny focused interfaces: `PriceProvider`, `RewardsProvider`, `ProductResolver`, `OfferProcessor`. |
| **Dependency Inversion** | `PriceComparisonService` depends on abstractions; concretes are injected by the composition root. |

## Run it

```bash
# from the project root
python3.11 -m venv .venv
source .venv/bin/activate

pip install -e ./backend            # install the domain core (editable)
pip install -r server/requirements.txt

cp server/.env.example server/.env  # add your SerpAPI key for live prices
uvicorn server.main:app --reload --port 8000
```

Open **http://localhost:8000**.

## Live prices vs. demo data

Without a `SERPAPI_KEY` in `server/.env` the agent serves **deterministic demo
data**, so the whole flow works offline. Add a free key from
[serpapi.com](https://serpapi.com/manage-api-key) for real prices. Check the
mode at `GET /api/health`.

## How a request flows

1. **Resolve** — `QueryResolver` turns the pasted URL / typed text into a
   `ProductQuery` (URL slug, page `og:title`, or plain text).
2. **Search** — a `PriceProvider` (SerpAPI Google Shopping, scoped to India)
   returns raw `Offer`s; `FallbackPriceProvider` drops to demo data if empty.
3. **Process** — a pipeline runs in order: `NoiseFilter` (drop accessories /
   refurb / outliers) → `Ranker` (dedupe, sort, cap) → `RewardsEnricher` (add
   live OnPoint cashback + onpoints).
4. **Respond** — the server maps the domain `ComparisonResult` to JSON; the
   frontend renders the "Earn with OnPoint" section and the full price list.

## Extending it

* **New price source** — implement `PriceProvider`, register it in
  `server/container.py:_build_provider`.
* **New resolver** — implement `ProductResolver`, add it to the chain in
  `_build_resolver`.
* **New processing step** — implement `OfferProcessor`, add it to the pipeline
  in `_build_pipeline`.

## Notes

- Query-based matching can still surface product variants (storage tiers,
  sellers); anchoring to one exact product URL is the only full fix.
- Local demo / prototype — not affiliated with OnPoint.
