---
name: img-gen-prompts
description: Search oip-visual-v2 for traceable prompt-image pairs and open local result galleries. Use when finding, inspecting, comparing, browsing, or copying real image-generation references or exact source prompts. After references are selected, adapt them into a derived bilingual prompt when requested; use img-gen-taste first when the visual direction is still unclear.
---

# Img Gen Prompts

Act as the evidence and retrieval layer. Use only the latest paired
`oip-visual-v2` archive. Every recommended record must include a real image,
unchanged source prompt, source URL, author, stable ID, and explainable match.
Never fall back to legacy/V1 data or generic web image search.

## Locate and verify the archive

Resolve this Skill's directory and run its bundled script by absolute path. It
finds the checkout from the current directory, a symlinked Skill path, or
`OIP_REPO_ROOT`; copied installations outside the checkout must set that
variable.

```bash
python3 <absolute-skill-directory>/scripts/oip.py status
```

Stop unless `ready` is true and the active taxonomy is exactly
`oip-visual-v2`. The current checkout is expected to contain the complete Git
LFS image corpus; if the archive, local images, or gallery dependencies are
missing, run `npm run setup` from the repository root before continuing. This
Skill is read-only: never activate a taxonomy, label records, publish data, or
modify the database.

## Search the user's actual intent

```bash
python3 <absolute-skill-directory>/scripts/oip.py search \
  --intent "雨夜霓虹小巷里的电影感人像" --limit 8

python3 <absolute-skill-directory>/scripts/oip.py get --id <tweet_id>
```

Pass the user's wording without embellishing it with guessed styles, subjects,
or negative constraints. Inspect `parsed_intent`, `match_reasons`, tags, and
`absolute_image_paths`; open representative images before judging quality.
Read `references/retrieval-contract.md` when interpreting constraints or an
empty result.

Treat `results` as exact matches. `related_results` is a separate fallback
channel that may omit exactly one declared aesthetic constraint. Never present
a related reference as an exact match: disclose its `missing_constraints` and
recommend only the visual decisions it actually demonstrates. Related
references are already restricted to image-confirmed visual evidence and
exclude unrequested screenshots, document graphics, heavy text, multi-panel
layouts, and watermarks.

For each recommendation return:

- stable ID, author, and source URL;
- representative image path;
- whether the match is `exact` or `related`;
- any declared `missing_constraints`;
- unchanged `source_prompt`;
- two or three meaningful match reasons;
- what visual decision is reusable and what should not be copied.

Translations and derived prompts are aids, never source prompts. If no relevant
result exists in either channel, report the corpus gap instead of inventing
provenance. The tool already performs the only allowed one-facet fallback;
never manually relax the subject, use, explicit style, scene, user invariants,
or forbidden constraints.

Some archive records contain commentary or post copy rather than an executable
generation prompt. Label that distinction clearly and do not present such text
as a reusable original prompt.

## Adapt selected references

When requested, synthesize the user's selected coherent references into a new
English prompt and a Simplified Chinese equivalent. Preserve any
`creative_spec` invariants and avoid list supplied by `$img-gen-taste`. Keep the
new prompt, rationale with source IDs, and original prompts clearly separated.
Do not copy a complete source prompt, identity, brand, protected character, or
unique scene.

## Let the user choose visually

When the user wants to browse or compare results, read
`references/gallery-session.md`, create a local result session, and open only
the URL returned by the command.

```bash
python3 <absolute-skill-directory>/scripts/oip.py gallery \
  --intent "克制的暗调香水广告" --lang zh-Hans --limit 8
```

The gallery must preserve search rank and keep “copy original prompt”
byte-for-byte faithful. If `url_usable` is false, run the returned
`start_command` before presenting the URL as openable.
