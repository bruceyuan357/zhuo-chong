# Artwork and icons

The garden and koi are original raster assets generated for this repository with the built-in ImageGen tool on 2026-10-15. The source PNG files are included here; runtime scaling, night tinting, sprite rotation and interactive particles are implemented by pygame. No image-generation service is called by the shipped application.

- `garden.png`: garden viewport background, 1586 × 992 pixels.
- `koi.png`: one fish sprite, 1536 × 1024 pixels, with real alpha transparency.

## Garden prompt

Use case: stylized-concept. Asset type: production background illustration for a native desktop pond companion, shown at 432 x 270 logical pixels; landscape 3:2 composition. Create one exquisite miniature water garden diorama seen from an elevated three-quarter angle. A broad, clear turquoise/jade pond occupies the central lower half (water surface from roughly 20% to 84% of image width and 45% to 85% height), surrounded by a low oval island of pale limestone, velvety moss, a graceful small pine tree on the left, delicate reeds on the right, and three lotus leaves at the edges. A tiny warm stone lantern on the right bank. Soft pale celadon mist and very faint distant mountain silhouettes fill the upper third, with calm negative space. Tactile matte clay / hand-painted gouache aesthetic, sophisticated and atmospheric, soft light from upper left, subtle water caustics, beautifully composed, organic restrained details, dreamy and peaceful. Palette: creamy warm mist, mineral jade, deep forest accents, tiny apricot light. The water must be EMPTY of fish, animals, rings or droplets because animated fish and interactive water ripples will be overlaid by the app. Fill the frame with the scene, no border. No text, typography, UI, icons, watermarks, labels, humans, literal desktop or devices. Crisp at small size, polished collectible miniature quality.

## Koi prompt

Use case: stylized-concept. Asset type: a single production game sprite on a genuinely transparent background. One elegant Japanese koi carp seen EXACTLY straight from above, whole body and delicate semi-translucent fins, swimming toward the RIGHT with its head at the right edge and tail at the left. White ivory body with tasteful vermilion red patches and a small warm gold accent. Realistic painterly miniature detail, soft shading, no directional cast shadow, no perspective. A slight graceful curve in the tail. Entire fish centered with 15% clear transparent padding all around, wide landscape canvas 3:2. Must read clearly at 40 pixels long. NO water, waves, stones, scenery, bubbles, border, checkerboard, text, icons or other fish. An isolated cutout with real alpha transparency, never an opaque background.

## Icons

PNG icons are derived from the official [Lucide source files](https://github.com/lucide-icons/lucide/tree/main/icons), retrieved 2026-10-15. The `circle-help` asset uses the [0.468.0 source](https://github.com/lucide-icons/lucide/blob/0.468.0/icons/circle-help.svg). Source SVGs were rasterized to white 72-pixel PNGs for runtime tinting, so users need only pygame. The complete upstream ISC / Feather MIT notices are retained in [icons/LICENSE](icons/LICENSE).
