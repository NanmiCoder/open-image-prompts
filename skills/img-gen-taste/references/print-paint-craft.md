# Printmaking, paper craft, ink and tactile painting style cards

These are general text-to-image visual grammars, not subject categories. Each
card was distilled from three distinct paired prompt-image sources in
`oip-visual-v2`. The sources establish corpus evidence; every card remains
generation-pending until it passes the blind generation gate.

## Limited-ink risograph editorial

- `id`: `limited-ink-risograph-editorial`
- `name_en`: Limited-Ink Risograph Editorial
- `name_zh`: 限色孔版印刷编辑图
- `validation_status`: corpus-reviewed / generation-pending
- `trigger`: Independent posters, zines, editorial illustrations, cultural programs and simple brand graphics that need tactile print energy.
- `not_for`: Photoreal products, subtle skin rendering, exact gradients, glossy luxury imagery or layouts whose small text must already be final.
- `visual_dna`: One to three spot inks plus the paper ground carry the whole image; halftone density creates volume; slight registration drift and paper grain reveal the print process; one bold silhouette or information hierarchy survives at thumbnail size.
- `composition_light_color_material`: One central subject or a clearly divided zine grid; cream or uncoated paper ground; one to three named spot inks; semi-transparent overprint may create secondary colors; shadows are dots, hatching or solid shapes rather than continuous gradients.
- `boundaries`: Preserve the requested subject, palette count and title-safe area. Use one dominant screening logic. Keep registration drift subtle and localized at selected edges, never as general blur. Omit readable text unless the user supplies exact copy. A city-landmark travel layout routes first to `retro-city-travel-poster`; dramatic comic storytelling routes first to `sixties-pop-comic`. Choose this card only when the print process itself is central.
- `template`: `A limited-ink risograph editorial illustration of [SUBJECT] for [USE], [ONE BOLD SILHOUETTE / CLEAR ZINE GRID], printed with exactly [INK 1], [INK 2] and optional [INK 3] on warm uncoated paper, form described by solid ink shapes and one consistent halftone screen, subtle paper tooth and slight edge-only registration drift, intentional overprint where colors meet, reserved [TITLE / COPY] area, no gradients, no glossy 3D, no invented text, no logo.`
- `anti_patterns`: Rainbow palette; random noise everywhere; photographic blur sold as misregistration; tiny illegible panels; fake vintage stains; mixing screen print, watercolor and chrome.
- `references`:
  - `tweet_id: 2065135532875645242`; `image_id: 15764`; `image: images/2065135532875645242/1.jpg`

## Layered papercraft diorama

- `id`: `layered-papercraft-diorama`
- `name_en`: Layered Papercraft Diorama
- `name_zh`: 分层纸雕场景
- `validation_status`: corpus-reviewed / generation-pending
- `trigger`: Storybook covers, nature scenes, warm campaign illustrations, window displays and simple scenes where physical depth should be immediately legible.
- `not_for`: Literal ecommerce photography, thin vector icons, liquid motion, transparent materials or scenes that depend on realistic hair and skin.
- `visual_dna`: A controlled stack of hand-cut paper planes creates foreground, subject and background; cut edges and cast shadows explain depth; simplified silhouettes and a restrained material palette keep the scene tactile rather than plastic.
- `composition_light_color_material`: Straight-on relief, framed shadowbox or gentle three-quarter diorama; several readable depth bands; one soft directional light; matte fiber paper with visible cut edges; foreground elements frame a clear focal opening.
- `boundaries`: Preserve the requested number of subjects, explicit layer count, colors, safe areas and aspect ratio. Paper remains the dominant material. Keep shadows physically consistent and layer order readable. Route rounded volumetric figures without visible cut planes to `handcrafted-clay-character` instead.
- `template`: `A handcrafted layered-papercraft diorama of [SUBJECT AND ACTION], built from [REQUESTED LAYER COUNT / A CONTROLLED STACK OF] clearly separated hand-cut matte paper planes, foreground framing a readable focal opening, visible paper fibers and clean cut edges, soft directional light from [DIRECTION] casting consistent shallow shadows between layers, restrained [PALETTE], [ASPECT RATIO] composition with [SAFE AREA] left open, no plastic, no clay, no floating pieces, no invented text, no logo.`
- `anti_patterns`: Hundreds of filigree layers; inconsistent light directions; glossy plastic edges; depth made only with blur; crowded decorative animals; mixed clay, fabric and paper; paper characters with realistic human skin.
- `references`:
  - `tweet_id: 2059228200841232771`; `image_id: 15173`; `image: images/2059228200841232771/4.jpg`
  - `tweet_id: 2066752996499927074`; `image_id: 17157`; `image: images/2066752996499927074/1.jpg`

## Minimalist ink-wash negative space

- `id`: `minimalist-ink-wash-negative-space`
- `name_en`: Minimalist Ink-Wash Negative Space
- `name_zh`: 极简水墨留白
- `validation_status`: corpus-reviewed / generation-pending
- `trigger`: Poetic landscapes, animals, plants, tea objects and contemplative editorial images where restraint and brush rhythm matter more than literal detail.
- `not_for`: Accurate diagrams, busy narrative scenes, colorful commercial packaging, photoreal portraits or requests that require crisp uniform linework.
- `visual_dna`: A few expressive strokes define the subject while untouched paper carries atmosphere; dry and wet ink, dark mass and pale wash, precise mark and dissolving edge form a controlled rhythm.
- `composition_light_color_material`: Asymmetric subject placement; more than half the field may remain untouched; black ink with optional one muted mineral accent; absorbent paper; depth comes from ink value and edge moisture, not perspective haze effects.
- `boundaries`: Preserve explicit prohibitions on calligraphy, seals and accent color. Use the fewest marks that keep the subject recognizable. One focal ink mass anchors the composition.
- `template`: `A minimalist [CHINESE INK WASH / SUMI-E] painting of [SUBJECT] in [SETTING], asymmetric composition with expansive untouched warm-white paper, a few confident brush strokes and pale wet-ink washes, controlled dry-brush texture at [FOCAL DETAIL], depth expressed through ink value and dissolving edges, poetic restraint, [OPTIONAL SINGLE MUTED ACCENT], no decorative border, no invented calligraphy, no seal stamp unless requested, no text, no logo.`
- `anti_patterns`: Filling every empty area; uniform digital outlines; automatic red seal or poem; gray fog over the entire image; random splatter; combining watercolor rainbow washes with monochrome ink logic.
- `references`:
  - `tweet_id: 2062404916174569621`; `image_id: 13948`; `image: images/2062404916174569621/1.jpg`
  - `tweet_id: 2066447081980473664`; `image_id: 16887`; `image: images/2066447081980473664/1.jpg`

## Expressive representational impasto

- `id`: `expressive-representational-impasto`
- `name_en`: Expressive Representational Impasto
- `name_zh`: 表现性具象厚涂
- `validation_status`: corpus-reviewed / generation-pending
- `trigger`: Portraits, still lifes and landscapes that need physical paint, decisive motion and emotionally amplified light while the subject remains recognizable.
- `not_for`: Flat brand graphics, precise technical illustration, delicate watercolor, clean vector art or abstract vortex covers already covered by `psychedelic-abstract-cover`.
- `visual_dna`: Thick palette-knife ridges follow the subject's form and movement; large value masses establish readability before detail; a restrained warm-cool opposition gives the paint a reason to catch light.
- `composition_light_color_material`: One dominant subject or natural force; medium or large brush groupings; optional glimpses of canvas at selected edges; directional light catches raised paint; one dominant color temperature with one or two counter-accents.
- `boundaries`: Preserve anatomy or scene structure beneath the brushwork. Put the thickest paint at the focal plane. Let background strokes simplify rather than compete. Use one coherent light direction.
- `template`: `An expressive figurative impasto oil painting of [SUBJECT] in [SETTING], recognizable structure established with large value masses, thick palette-knife ridges and loaded brushstrokes following [FORM / MOTION], strongest paint buildup at [FOCAL AREA], directional [LIGHT] catching the raised pigment, restrained warm-cool palette of [THREE COLOR FAMILIES], selected raw-canvas edges and simplified background, tactile physical oil paint, no smooth airbrush, no uniform texture, no photographic depth-of-field, no text, no logo.`
- `anti_patterns`: Equal texture on every surface; anatomy dissolved into paint noise; rainbow color with no hierarchy; digitally embossed filter; tiny decorative strokes; copying a named living artist; mixing literal 3D objects into the canvas.
- `references`:
  - `tweet_id: 2034607349856358836`; `image_id: 1633`; `image: images/2034607349856358836/1.jpg`
  - `tweet_id: 2056117434508022104`; `image_id: 10536`; `image: images/2056117434508022104/1.jpg`
