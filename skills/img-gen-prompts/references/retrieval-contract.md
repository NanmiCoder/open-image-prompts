# Retrieval contract

## Product boundary

This Skill is read-only and serves only the active `oip-visual-v2` corpus. It
must fail closed when another taxonomy is active. Labeling, provider routing,
queue recovery, taxonomy activation, database publication, and archive writes
belong to repository operations, not this user-facing Skill.

## Search pipeline

1. Pass the user's original wording to search. Do not silently enrich it with
   guessed subjects, styles, props, or negative constraints.
2. Treat an explicit `--tag` as locked. Literal request terms and core subject
   concepts may become must constraints; inferred preferences remain should
   constraints. Inspect `parsed_intent` instead of assuming which mode was used.
3. Recall from both prompt labels and image labels. Prefer image-confirmed
   evidence and default to records with local images.
4. Penalize objective quality flags such as `needs-review` and
   `visible-artifacts`. Do not invent a subjective “beauty score”.
5. Diversify near-duplicate tags and authors after relevance ranking.
6. Explain matched constraints for every result.

## Stable output

Search output uses schema `oip-retrieval-v1` and includes:

- exact taxonomy version;
- raw and parsed intent;
- ranked result score and match reasons;
- unchanged source prompt and bilingual translations;
- canonical tags and all image paths;
- author and source URL.

Results without a real image, source prompt, author/source provenance, or stable
tweet ID are invalid.

`source_prompt` is the unchanged source text stored by the archive. When that
text is commentary, an announcement, or post copy rather than an executable
generation prompt, disclose the distinction instead of relabeling it.

## Empty and relaxed results

Zero relevant results are better than unrelated examples. Retry at most once
after removing one non-core mood, lighting, or palette preference from the
query. State what changed. Never relax the subject, explicit style/use, locked
tags, user invariants, or forbidden constraints. If the archive still cannot
support the request, report that limitation and hand off to first-principles
prompting without fabricated provenance.
