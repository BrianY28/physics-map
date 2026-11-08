# Brief: shorten the Newton's first law explainer

The context file `explainers/first-law/index.html` is a reviewed, working explainer page. Readers find it too long: about 1,560 words of prose around three interactive plates. Produce a shorter version of the same file. It becomes the template every future explainer in the repository follows.

## Keep exactly
- The three plates (Plate I friction dial, Plate II Galileo's two ramps, Plate III braking bus) with all their HTML, ids, controls, readouts, notes and JavaScript behaviour. Do not change simulation logic, numbers or the status-note texts inside the plates.
- The visual design: CSS tokens, fonts, dark mode, layout, the `.sym` spans that keep symbols out of uppercase.
- The page rules: no doctype/html/head/body tags; starts with `<title>Newton's First Law</title>`, then `<meta name="claude:viewport-fit-sides" content="cover">`, then the Google Fonts link, then one `<style>`; colors only as tokens; side gutters with max(16px, env(...)); works at 400px; no external scripts.
- These reviewed facts, worded as now: the Latin of Lex I and Motte's 1729 English ("Every body perseveres in its state of rest, or of uniform motion in a right line, unless it is compelled to change that state by forces impress'd thereon."); a = μg with g = 9.81 m/s²; d = h / sin θ; the bus braking at 5.0 m/s² from 4.0 m/s; the fictitious force −m·a_bus; Galileo's inertia was horizontal motion along the Earth's surface; Descartes (Principles of Philosophy, 1644) first stated straight-line inertia; Philoponus (6th century, Alexandria); Buridan (14th century, impetus proportional to quantity of matter and speed); Voyager 1 (launched 1977, interstellar space since 2012, about 17 km/s relative to the Sun, motion nearly but not exactly uniform because of the Sun's weak gravity).

## New structure and word budget (prose outside the plates: 600 words at most)
1. Masthead: breadcrumb, kicker, h1, one-sentence standfirst, and two small links: "View in the physics map" and "Edit this node on GitHub" (URLs below).
2. § 1 The law (about 90 words): the Latin and English quote with its caption; the plain one-sentence statement; one short paragraph saying uniform motion means constant velocity (speed and direction) and rest is the special case of zero velocity. Drop the paragraph about "nisi quatenus".
3. § 2 Friction dial (about 70 words): 2-3 sentences of setup above Plate I, then one line under it: "Common mistake: 'Moving things need a force to keep moving.'" followed by one or two sentences of correction.
4. § 3 Galileo's two ramps (about 80 words): setup in 2-3 sentences including the 1632/1638 attribution, Plate II, then "Common mistake: 'Objects naturally slow down.'" with one or two sentences.
5. § 4 Which frame? (about 110 words): setup in 2-3 sentences, Plate III, then "Common mistake: 'The first law is just F = ma with F = 0.'" with the frame argument and the −m·a_bus fictitious force in 2-3 sentences.
6. § 5 Where you meet it (about 70 words): seat belts, the tablecloth trick and Voyager 1, one sentence each.
7. A closed-by-default `<details>` block, summary "How the idea arrived: Aristotle to Newton", holding the six-entry timeline with each entry cut to at most 20 words. Style it to match the page; keyboard accessible.
8. Sources (a short list, small type):
   - Newton, I. (1687). Philosophiae Naturalis Principia Mathematica. London.
   - Newton, I. (1729). The Mathematical Principles of Natural Philosophy (A. Motte, Trans.). London: Benjamin Motte.
   - Galilei, G. (1632). Dialogo sopra i due massimi sistemi del mondo. Florence.
   - Galilei, G. (1638). Discorsi e dimostrazioni matematiche intorno a due nuove scienze. Leiden: Elzevir.
   - Descartes, R. (1644). Principia Philosophiae. Amsterdam: Elzevir.
9. Footer "In the map": the breadcrumb and three links:
   - "View the full map": https://briany28.github.io/physics-map/
   - "Edit this node on GitHub": https://github.com/BrianY28/physics-map/blob/main/nodes/01-newtonian-mechanics/newtons-laws.md
   - "Report a mistake": https://github.com/BrianY28/physics-map/issues/new/choose
   All as normal anchors with target="_blank" rel="noopener". Remove every MindNode link.

Renumber the sections to match. Remove the separate "Three misconceptions" and long "How the idea arrived" sections; their content moves into the "Common mistake" lines and the details block. Plain, direct sentences in active voice; no em-dash asides.

Return the complete file as `explainers/first-law/index.html`.
