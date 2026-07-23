# Poster and cover style cards

Reserve explicit space for typography, but never ask the image model to invent body copy. Add final copy in a design tool when exact spelling matters.

## Retro city travel poster

- `id`: `retro-city-travel-poster`
- `name_en`: Retro City Travel Poster
- `name_zh`: 复古城市旅行海报
- `validation_status`: experimental-corpus-reviewed / generation-pending (single-source cluster)
- `trigger`: Destination posters, tourism campaigns, landmark souvenirs, city series and nostalgic print art.
- `not_for`: Factual maps, photoreal travel photography, dense itineraries, modern luxury ads.
- `visual_dna`: One iconic landmark reduced to a heroic silhouette; large sun disc or simple atmospheric field; limited spot colors; screen-printed grain; cream border; civic optimism.
- `composition_light_color_material`: Vertical 2:3 or 3:4; landmark dominates middle; city name occupies a clean bottom band; low-detail supporting skyline; two to four inks such as vermilion, teal, navy, ochre and cream; worn lithographic paper.
- `boundaries`: Use one landmark and one geographic cue. Keep small details subordinate. Generate without wording when the final city label will be typeset later.
- `template`: `A vintage mid-century travel poster for [CITY], featuring [ICONIC LANDMARK] as one heroic simplified silhouette against [SUN / SKY / WATER], vertical 2:3 composition, low supporting skyline, limited screen-print palette of [3-4 COLORS], cream paper border, subtle halftone and worn lithographic grain, optimistic civic mood, clean empty title band at the bottom, no invented text, no logo.`
- `anti_patterns`: Photographic collage; ten landmarks; modern gradient mesh; tiny itinerary copy; generic suitcase icons; excessive distress that hides the image.
- `references`:
  - `tweet_id: 2058464433698168983`; `image_id: 11933`; `image: images/2058464433698168983/1.jpg`
  - `tweet_id: 2058464433698168983`; `image_id: 11934`; `image: images/2058464433698168983/2.jpg`
  - `tweet_id: 2058464433698168983`; `image_id: 11935`; `image: images/2058464433698168983/3.jpg`

## Monochrome editorial city poster

- `id`: `monochrome-editorial-city-poster`
- `name_en`: Monochrome Editorial City Poster
- `name_zh`: 黑白编辑式城市海报
- `validation_status`: corpus-reviewed / generation-pending
- `trigger`: Architecture exhibitions, city editorials, cultural events, magazine covers and restrained premium travel campaigns.
- `not_for`: Children's art, colorful tourism, action films, information-dense infographics.
- `visual_dna`: Stark black-and-white architectural photograph; strict modular grid; oversized grotesk country heading crossed by elegant display script; coordinates and microcopy used as texture; abundant white field.
- `composition_light_color_material`: Vertical page; one bordered monochrome photo centered or low; large top heading; deliberate asymmetric metadata; deep blacks, white and grey only; subtle newspaper grain.
- `boundaries`: Typography hierarchy has three levels maximum. Use real copy supplied by the user or empty marked zones. One photograph only. Do not decorate with icons beyond small metadata marks.
- `template`: `A premium monochrome editorial poster for [CITY / BUILDING], one high-contrast black-and-white architectural photograph inside a strict rectangular frame, oversized bold grotesk heading zone at the top, elegant script-title zone crossing the image, sparse coordinates and microcopy zones aligned to a modular Swiss grid, generous white margins, subtle newspaper grain, vertical print layout, no invented text, no logos.`
- `anti_patterns`: Centering every element; colorful accents; multiple photos; fake dense paragraphs; ornamental borders; weak grey contrast.
- `references`:
  - `tweet_id: 2031799622071357760`; `image_id: 259`; `image: images/2031799622071357760/1.jpg`
  - `tweet_id: 2031799572092129399`; `image_id: 260`; `image: images/2031799572092129399/1.jpg`
  - `tweet_id: 2031798409472995760`; `image_id: 262`; `image: images/2031798409472995760/1.jpg`

## Monumental 3D word poster

- `id`: `monumental-3d-word-poster`
- `name_en`: Monumental 3D Word Poster
- `name_zh`: 纪念碑式三维大字海报
- `validation_status`: experimental-corpus-reviewed / generation-pending (single-source cluster)
- `trigger`: Campaign key visuals, team launches, film-concept posters, motivational themes and event hero banners with one powerful word.
- `not_for`: Paragraph copy, subtle editorial design, small product listings, whimsical illustration.
- `visual_dna`: A single gigantic extruded word acts as architecture; people or characters establish scale; material encodes the concept; mostly white or minimal stage; forward-moving group creates conviction.
- `composition_light_color_material`: Wide 16:9; eye-level centered symmetry; letters fill the rear two-thirds; figures walk toward camera; controlled studio/volumetric light; one concept material such as ember, galaxy, black steel or ice.
- `boundaries`: One short word, ideally 4-8 Latin letters. Spell it exactly and repeat it in a separate typography instruction. One material metaphor only. Keep supporting copy out of generation.
- `template`: `A cinematic wide 16:9 campaign poster built around the exact single word "[WORD]" as colossal extruded 3D architecture, letters made from [ONE CONCEPT MATERIAL], a coordinated group of [CHARACTERS] walking toward camera to establish scale, centered eye-level symmetry, clean minimal [WHITE / DARK] stage, controlled rim and volumetric light, premium realistic materials, decisive heroic mood, no other words, no logo.`
- `anti_patterns`: Long sentence as sculpture; mixed fire-water-space materials; characters hiding letter shapes; unreadable decorative font; busy background; many slogans.
- `references`:
