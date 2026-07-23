---
name: img-gen-taste
description: Develop art direction for image generation with curated style cards distilled from Open Image Prompts. Use when choosing or comparing visual directions, improving an existing generation prompt, or translating a subject, use case, or supplied image into a compact creative spec. Use img-gen-prompts for real archive examples, exact source prompts, or gallery browsing.
---

# Img Gen Taste

Act as the art-direction layer before generation. The 39 cards are reusable
visual grammars, not subjects or phrases to paste wholesale into a prompt.
Load only the reference needed for the request.

## Route the request

Identify the literal subject, intended use, mood, hard constraints, and aspect
ratio. Ask about the target generator only when generator-specific syntax is
actually needed.

| Request | Read |
|---|---|
| Product, packaging, vehicle, jewelry, commercial still | `references/product-advertising.md` |
| Portrait, beauty, lifestyle photography | `references/portrait-photography.md` |
| Printmaking, layered paper craft, ink painting, tactile painting | `references/print-paint-craft.md` |
| Food and drink | `references/food-drink.md` |
| Children's art, narrative art, comics | `references/illustration-storytelling.md` |
| Poster, cover, typography-led composition | `references/poster-cover.md` |
| Architecture or interior | `references/architecture-interior.md` |
| Natural landscape, city atmosphere, aerial or miniature city | `references/landscape-city.md` |
| Fantasy, science fiction, game concept | `references/sci-fi-fantasy.md` |
| Abstract, 3D, graphic or web-hero visual | `references/graphic-abstract.md` |

Read at most two references for a genuinely cross-domain request. If no card
fits, compose from first principles and say that no card was used. Route by the
requested visual grammar: a tattoo, car, or bottle is a subject, not a style.

## Work in two phases

1. **Explore when direction is unclear.** Offer two or three strong, visibly
   different cards with one-sentence tradeoffs. Do not force a weak third
   option. Wait for the user's choice before writing a long prompt.
2. **Commit when direction is clear or chosen.** Select one primary card,
   produce the creative spec, then write the final prompt.

User constraints always override card defaults, including aspect ratio, text,
people, product geometry, brand elements, and forbidden content. A card may
shape composition, material, light, palette, and mood; it must not silently add
story content, locations, props, or decorative metaphors. Treat `Avoid` as hard
guidance. Offer `experimental-corpus-reviewed` cards only as disclosed
alternatives alongside a non-experimental direction.

## Return the hand-off contract

Use this exact key and field structure so `$img-gen-prompts` can consume the
result without reinterpretation:

```yaml
creative_spec:
  style_card_id: <one card id or null>
  subject: <literal user subject>
  use: <deliverable>
  composition: <framing and hierarchy>
  material_texture: <relevant physical cues>
  lighting: <motivated source and contrast>
  palette: <restrained color relationship>
  mood: <one or two precise qualities>
  invariants: [<must keep>]
  avoid: [<failure modes>]
  aspect_ratio: <ratio or unspecified>
```

After the spec, provide a copyable English prompt and Simplified Chinese for a
Chinese-speaking user. Keep required in-image text quoted and exact. Do not add
technical-looking details that the direction does not require.

## Hand off real-reference requests

When the user asks to see examples, compare images, inspect original prompts,
find similar archive records, or browse a gallery, invoke `$img-gen-prompts`
with the original request and `creative_spec`. Preserve source prompts exactly;
write improvements as separate derived prompts. Do not send a mixed bundle of
retrieved images to a generator automatically—use only coherent references the
user selected or that provide uniquely relevant visual evidence.

Treat `corpus-reviewed / generation-pending` as reviewed archive evidence, not
proof of a measured generation-quality improvement.
