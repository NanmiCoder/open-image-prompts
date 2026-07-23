# Public dataset

The distributable archive is `db/prompts.db.gz`. It expands into an immutable, read-only SQLite database at runtime.

## Included tables

- `prompts`
- `images`
- `prompt_translations`
- `label_dimensions`
- `labels`
- `taxonomy_labels`
- `prompt_labels`
- `media_labels`
- `prompt_fts` and its SQLite-managed shadow tables
- `archive_config`, containing only the active public taxonomy version

Operational labeling tables and fields are intentionally absent. Public label rows contain only record IDs, taxonomy IDs, and confidence values; model names, providers, sources, evidence, run IDs, rationales, errors, leases, candidate labels, and timestamps from internal processing are not exported.

## Image selection

Local image files are present only when the versioned public-image decision is both `generated` and `allow`. Every included file has exactly one `images.local_path` row, and every public DB image row has exactly one local file.

The selection is a conservative publishing boundary, not a statement about copyright ownership or suitability for every jurisdiction. See `DATA_LICENSE.md`.

## Manifest

`data/public-corpus.json` records the dataset version, taxonomy version, image-policy snapshot, row counts, and source-archive digest. Run `npm run verify:data` to check SQLite integrity, DB/file correspondence, and image signatures.
