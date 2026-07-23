# Open Image Prompts Web

React and Vite gallery for exploring the image and prompt collection.

Run commands from the repository root:

```bash
npm run setup
npm run dev
```

The first run expands `../db/prompts.db.gz` once under the ignored
`.oip/runtime/` directory. The cross-platform Node launcher finds Python,
starts the read-only SQLite API, and then starts Vite. The browser fetches
paginated JSON while Vite serves approved Git LFS images from `../images/`.

Useful environment variables:

- `OIP_DB_PATH`: decompressed SQLite path.
- `OIP_DB_ARCHIVE_PATH`: source `.db.gz` path.
- `OIP_API_HOST`: API bind address (default `127.0.0.1`).
- `OIP_API_PORT`: API port (default `8787`).
- `OIP_API_QUERY_CONCURRENCY`: maximum concurrent SQLite page/search queries
  (default `4`).
- `OIP_API_QUERY_WAIT_SECONDS`: how long a request waits for a query slot before
  receiving `503` (default `3`).
- `OIP_API_CACHE_ENTRIES`: maximum in-memory paginated response cache entries
  (default `128`).

Search uses the archive's SQLite FTS5 index across source prompts,
translations, authors, tools, and visual labels. The API bounds concurrent
queries and keeps a small LRU response cache so one busy search cannot create
an unbounded number of SQLite scans. Search text is submitted explicitly with
Enter or the Search button, so typing and IME composition do not trigger API
requests.

`npm run preview` builds the frontend and runs the production preview with the
same local API and image service on Windows, macOS, and Linux.
