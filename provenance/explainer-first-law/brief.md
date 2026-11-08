# Brief: interactive explainer for Newton's first law

Write one self-contained HTML page that teaches Newton's first law (inertia) to a curious adult with high-school physics. It belongs to a mind map called "Physics: From Newton to the Frontier"; this page explains one node of it.

## Source of truth from the reviewed map (keep consistent with it)
- Node path: Physics: From Newton to the Frontier › Newtonian mechanics › Newton's laws › First law: inertia
- Newton's laws (1687, Isaac Newton): "The Principia states three laws: inertia, force proportional to change of motion, and equal and opposite action-reaction, giving F = dp/dt (commonly F = ma). Together they define inertial frames and reduce mechanics to solving differential equations."
- First law: inertia: "A body persists in uniform motion unless acted on by a net force, which implicitly defines the inertial frames where the laws hold."

## Content the page must cover
1. The law itself. Quote Lex I from the Principia in Latin and in Andrew Motte's 1729 English translation (both public domain). Then restate it in one plain sentence. Make clear that "uniform motion" means constant velocity: constant speed AND constant direction, and that rest is the special case of zero velocity.
2. Interactive 1, "Friction dial": a puck slides along a level track with a starting speed. A slider sets the friction coefficient μ from 0.30 down to 0. The puck decelerates at a = μg (g = 9.81 m/s²). Show a live speed-versus-time graph and readouts for μ, net force per kg, and current speed in m/s. At μ = 0 the speed stays constant and the puck wraps around or the track scrolls so it visibly never stops. Include Start/Reset controls.
3. Interactive 2, "Galileo's two ramps": a ball released from height h rolls down one ramp and up a second ramp with no friction, reaching the same height. A slider lowers the second ramp's angle θ (for example from 45° to 0°). The distance travelled up the second ramp is h / sin θ, so it grows as θ shrinks; at θ = 0 the ball rolls on forever. Show the distance as a number. Attribute the thought experiment correctly to Galileo (Dialogue, 1632; Two New Sciences, 1638).
4. Interactive 3, "Which frame?": a bus brakes while a ball rests on its floor, with no friction between ball and floor. A toggle switches between "Street view" (ground frame: the ball keeps moving at constant velocity while the bus slows) and "Passenger view" (bus frame: the ball appears to accelerate forward with no force acting on it). Use this to explain that the first law holds only in inertial frames, and that this is why the first law is not just a special case of the second law: it says which frames the second law applies in.
5. Misconceptions, each stated and corrected: "Moving things need a force to keep moving" (Aristotle's view); "Objects naturally slow down" (friction and drag are forces); "The first law is just F = ma with F = 0".
6. A short, accurate history: Aristotle, the medieval impetus theory (John Philoponus, Jean Buridan), Galileo (his inertia was horizontal motion over the Earth's surface), Descartes (first to state straight-line inertia, Principles of Philosophy, 1644), Newton (1687). Be careful with these attributions and dates.
7. Everyday and real examples: seat belts, the tablecloth trick, and a spacecraft coasting (for example Voyager 1, launched 1977, still moving at about 17 km/s relative to the Sun with no engine burning). Only use numbers you are sure of.
8. A section that places the page in the map: show the node path above as a breadcrumb and give two links, as normal anchor tags with target="_blank" rel="noopener":
   - "Open this node in the mind map": https://mindnode.com/document/3hq16XnASSIHX4fAHcm4wA/node/2f9wEGkux499WIIdqz8F9g
   - "Open the full mind map": https://mindnode.com/document/3hq16XnASSIHX4fAHcm4wA
   Add one line saying the map opens in MindNode for people who have access to it. Also put a compact link to the node near the top of the page.

## Rules the page must follow (it is published as a claude.ai Artifact)
- Write only the page content. Do NOT include <!DOCTYPE>, <html>, <head> or <body> tags; the host wraps the file in its own skeleton.
- The file starts with: <title>Newton's First Law</title>, then <meta name="claude:viewport-fit-sides" content="cover">, then one <style> block.
- Colors: define every color as a CSS custom property on bare :root (light values). Redefine the same tokens for dark mode in BOTH `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { ...; color-scheme: dark } }` AND `:root[data-theme="dark"] { ...; color-scheme: dark }`. Components use only tokens, never literal colors. body sets `background: var(--bg-token)` and `color` from tokens. Canvas drawing must read colors from the CSS tokens at draw time (getComputedStyle) and redraw when the color scheme changes.
- Layout: the outer wrapper (or body) has `padding-left: max(16px, env(safe-area-inset-left, 0px))` and `padding-right: max(16px, env(safe-area-inset-right, 0px))`, vertical padding via `padding-block` only. Must work at 400px wide with no horizontal page scroll. Canvases scale to their container width (handle devicePixelRatio and resize). Running text about 65 characters wide.
- Fonts: Google Fonts only (`<link rel="stylesheet" href="https://fonts.googleapis.com/css2?...&display=swap">` may go right after the meta tag), each with a real fallback stack. Do not use Inter or Space Grotesk.
- No external scripts, images or other resources. Use plain JavaScript and <canvas> or inline SVG. No libraries.
- Never use alert(), confirm(), prompt() or window.print(). No localStorage.
- Every form control has a stable id and a visible <label>. Keyboard focus is visible. Respect prefers-reduced-motion (start animations paused or reduce motion). The page must be complete and readable at rest: nothing hidden behind opacity:0 waiting for scroll; each simulation draws a meaningful first frame before any click.
- Design: give it a distinctive visual identity that fits classical mechanics (for example the look of a physics lab notebook, engraving plates of the Principia, or an air-track lab), not a generic template. Avoid: purple-to-blue gradient heroes, cream-and-terracotta, emoji as section markers, centering everything, the same rounded card and shadow on every block. Headings use text-wrap: balance.
- Copy: plain, direct sentences in active voice. No em-dash asides, no "not X, but Y" framing.
- Physics must be correct: units, formulas (a = μg, d = h / sin θ), and the frame argument.

## Output format
Return the complete file inside ONE ```html code fence and nothing else.
