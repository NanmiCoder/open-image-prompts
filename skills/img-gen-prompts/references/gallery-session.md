# Gallery session contract

Use a gallery session when the user wants to inspect the ranked references in
the browser. The session is a local hand-off artifact, not a database table and
not a source of truth.

## Create and open a result set

Run the bundled script by its absolute path. It locates the repository through
the current directory, a symlinked Skill path, or `OIP_REPO_ROOT`. A copied
installation outside the checkout must set `OIP_REPO_ROOT`.

```bash
python3 <absolute-skill-directory>/scripts/oip.py gallery \
  --intent "雨夜霓虹女性肖像" \
  --lang zh \
  --limit 8 \
  --derived-zh "一张可直接用于生成的中文提示词" \
  --derived-en "A copy-ready English generation prompt" \
  --open
```

The command searches the active `oip-visual-v2` archive, writes an ignored
`.oip/sessions/<uuid>.json` file, starts the owned gallery process, and returns
a URL shaped like:

```text
http://127.0.0.1:4173/?session=<uuid>&focus=<tweet_id>&lang=zh
```

Use `--creative-spec '<json-object>'` to preserve the style playbook hand-off.
Use `--no-start` when an owned gallery server is already available and only a
new session file and URL are needed. The response always includes
`url_usable`. When it is `false`, the printed URL is only a staged link; run the
returned `start_command` before presenting it as openable.

## Session behavior

- `references` is authoritative for membership and order.
- `focus` must be one of those references and opens its prompt dialog.
- `derived_prompt.en` and `derived_prompt.zh-Hans` are agent-authored outputs.
- The frontend copies a derived prompt only from the session panel.
- Every source card and dialog continues to copy `prompts.prompt_text` exactly.
- Missing reference IDs are reported by the frontend and are never replaced by
  unrelated archive items.
- The frontend ignores a session whose taxonomy is not `oip-visual-v2`.

## Process ownership

```bash
python3 <absolute-skill-directory>/scripts/oip.py start --port 4173
python3 <absolute-skill-directory>/scripts/oip.py status
python3 <absolute-skill-directory>/scripts/oip.py stop
```

The server binds only `127.0.0.1`. Runtime state lives under `.oip/`. `stop`
requires both the stored PID and the instance-specific local health response to
match before it sends a signal, so it cannot stop an unrelated reused PID.

The local bridge serves `/_oip/sessions/<uuid>.json` and proxies all other
requests to the repository's Vite gallery. The gallery resolves only the
session's stable IDs through the read-only SQLite API, then restores the
session's authoritative ranking. No API key belongs in a session.
