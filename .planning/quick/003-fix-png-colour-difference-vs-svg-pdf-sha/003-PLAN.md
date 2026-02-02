---
phase: quick
plan: 003
type: execute
wave: 1
depends_on: []
files_modified:
  - src/codepicture/render/shadow.py
  - tests/test_render_shadow.py
autonomous: true

must_haves:
  truths:
    - "PNG output has identical colours to SVG/PDF for the same theme and code"
    - "Red/blue channels are not swapped in PNG shadow output"
    - "A test verifies colour correctness through the shadow pipeline"
  artifacts:
    - path: "src/codepicture/render/shadow.py"
      provides: "Correct BGRA-to-RGBA channel conversion"
    - path: "tests/test_render_shadow.py"
      provides: "Colour preservation regression test"
  key_links:
    - from: "src/codepicture/render/shadow.py"
      to: "cairo.ImageSurface"
      via: "BGRA byte extraction and Pillow conversion"
      pattern: "Image\\.frombytes"
---

<objective>
Fix PNG colour difference vs SVG/PDF caused by incorrect BGRA-to-RGBA channel conversion in the shadow post-processing pipeline.

Purpose: Cairo ImageSurface uses FORMAT_ARGB32 which stores pixels in native byte order (BGRA on little-endian). The current code reads this as Pillow "RGBa" mode, which handles pre-multiplied alpha un-premultiplication but does NOT swap B and R channels. This causes red and blue channels to be swapped in all PNG output that goes through `apply_shadow()` (both shadow-enabled and shadow-disabled paths).

Output: Corrected shadow.py with proper channel handling, plus a regression test that verifies a known colour drawn via Cairo survives the shadow pipeline intact.
</objective>

<execution_context>
@/Users/bartel/.claude/get-shit-done/workflows/execute-plan.md
@/Users/bartel/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@src/codepicture/render/shadow.py
@src/codepicture/render/canvas.py
@src/codepicture/render/renderer.py
@tests/test_render_shadow.py
@src/codepicture/core/types.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix BGRA channel swap in shadow.py</name>
  <files>src/codepicture/render/shadow.py</files>
  <action>
  In `apply_shadow()`, the conversion from Cairo ImageSurface bytes to Pillow Image is incorrect.

  Cairo FORMAT_ARGB32 stores pixels as 32-bit values in native byte order. On little-endian systems (all modern x86/ARM), the byte layout in memory is B, G, R, A. The Pillow "RGBa" mode interprets bytes as R, G, B, premultiplied-a -- it un-premultiplies alpha but does NOT reorder channels. So R and B end up swapped.

  Fix approach -- replace lines 79-82 with proper channel handling:

  ```python
  # CRITICAL: Cairo FORMAT_ARGB32 stores pixels as native-endian uint32.
  # On little-endian systems the byte layout is B, G, R, A.
  # Pillow's "RGBa" mode expects R, G, B, premultiplied-a and does NOT
  # swap channels -- it only un-premultiplies alpha.
  # We must read as raw BGRA, swap B<->R, then handle pre-multiplied alpha.
  data = bytes(surface.get_data())
  # Read raw bytes as RGBA (will have B/R swapped)
  pil_image = Image.frombytes("RGBa", (width, height), data)
  pil_image = pil_image.convert("RGBA")
  # Swap R and B channels to correct Cairo's BGRA byte order
  b, g, r, a = pil_image.split()
  pil_image = Image.merge("RGBA", (r, g, b, a))
  ```

  Note: The "RGBa" mode is still needed to handle pre-multiplied alpha un-premultiplication. After converting to "RGBA" we then swap R and B. This two-step approach is necessary because Pillow has no "BGRa" mode for pre-multiplied BGRA.

  Also apply the same fix to the `enabled=False` path (lines 67-71). Currently the disabled path uses `surface.write_to_png()` which is Cairo's own PNG writer and handles BGRA->RGBA internally, so that path is correct. Only the `enabled=True` path needs fixing.

  Verify by examining both code paths: the `enabled=False` path uses Cairo's `write_to_png()` (correct), the `enabled=True` path must swap B and R after Pillow conversion.
  </action>
  <verify>
  Run existing shadow tests to confirm no regression:
  `cd /Users/bartel/Documents/newclone/codepicture && uv run pytest tests/test_render_shadow.py -v`

  Then generate test outputs and visually compare:
  `cd /Users/bartel/Documents/newclone/codepicture && uv run codepicture tests/fixtures/sample.py -o /tmp/test_fix.png`
  `cd /Users/bartel/Documents/newclone/codepicture && uv run codepicture tests/fixtures/sample.py -o /tmp/test_fix.svg`
  </verify>
  <done>The B and R channels are correctly swapped in the shadow pipeline. PNG colours match SVG/PDF output.</done>
</task>

<task type="auto">
  <name>Task 2: Add colour preservation regression test</name>
  <files>tests/test_render_shadow.py</files>
  <action>
  Add a new test class `TestShadowColorPreservation` to `tests/test_render_shadow.py` that verifies colours survive the shadow pipeline without channel swapping.

  The test should:
  1. Create a CairoCanvas at scale=1.0 (to avoid HiDPI coordinate complications)
  2. Draw a known-colour filled rectangle (e.g., Color(255, 0, 0) pure red) covering the full canvas
  3. Pass the surface through `apply_shadow(surface, enabled=True)`
  4. Load the resulting PNG bytes with Pillow
  5. Sample a pixel from the CENTER of the image (inside the shadow margin, on the actual content) and assert:
     - R channel == 255 (or close, within tolerance of 2 due to alpha compositing at edges)
     - G channel == 0
     - B channel == 0 (would be 255 if bug still present)

  Add a second test with Color(0, 0, 255) pure blue to confirm it's not accidentally passing due to symmetry.

  Add a third test for the `enabled=False` path to confirm it also preserves colours (this is the baseline).

  Use `from PIL import Image` and `from io import BytesIO` for loading the output PNG.

  ```python
  class TestShadowColorPreservation:
      """Regression: verify shadow pipeline does not swap R/B channels."""

      def test_red_stays_red_with_shadow(self):
          canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
          canvas.draw_rectangle(0, 0, 100, 100, Color(255, 0, 0))
          data = apply_shadow(canvas._surface, enabled=True)

          from PIL import Image
          from io import BytesIO
          img = Image.open(BytesIO(data)).convert("RGBA")
          # Sample center pixel (content is at shadow_margin offset)
          margin = calculate_shadow_margin()
          r, g, b, a = img.getpixel((margin + 50, margin + 50))
          assert r == 255, f"Red channel should be 255, got {r}"
          assert g == 0, f"Green channel should be 0, got {g}"
          assert b == 0, f"Blue channel should be 0, got {b}"

      def test_blue_stays_blue_with_shadow(self):
          canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
          canvas.draw_rectangle(0, 0, 100, 100, Color(0, 0, 255))
          data = apply_shadow(canvas._surface, enabled=True)

          from PIL import Image
          from io import BytesIO
          img = Image.open(BytesIO(data)).convert("RGBA")
          margin = calculate_shadow_margin()
          r, g, b, a = img.getpixel((margin + 50, margin + 50))
          assert r == 0, f"Red channel should be 0, got {r}"
          assert g == 0, f"Green channel should be 0, got {g}"
          assert b == 255, f"Blue channel should be 255, got {b}"

      def test_color_preserved_without_shadow(self):
          canvas = CairoCanvas.create(100, 100, OutputFormat.PNG, scale=1.0)
          canvas.draw_rectangle(0, 0, 100, 100, Color(255, 0, 0))
          data = apply_shadow(canvas._surface, enabled=False)

          from PIL import Image
          from io import BytesIO
          img = Image.open(BytesIO(data)).convert("RGBA")
          r, g, b, a = img.getpixel((50, 50))
          assert r == 255, f"Red channel should be 255, got {r}"
          assert g == 0, f"Green channel should be 0, got {g}"
          assert b == 0, f"Blue channel should be 0, got {b}"
  ```
  </action>
  <verify>
  `cd /Users/bartel/Documents/newclone/codepicture && uv run pytest tests/test_render_shadow.py -v`

  All tests pass including the 3 new colour preservation tests.
  </verify>
  <done>Three regression tests confirm: red stays red, blue stays blue, and colours are preserved in both shadow-enabled and shadow-disabled paths.</done>
</task>

</tasks>

<verification>
1. `uv run pytest tests/test_render_shadow.py -v` -- all tests pass
2. `uv run pytest tests/ -v --timeout=30` -- full test suite passes (no regression)
3. Generate PNG and SVG of the same file and visually confirm colours match
</verification>

<success_criteria>
- PNG output colours match SVG/PDF output for the same code and theme
- Red/blue channels are not swapped in shadow pipeline
- 3 new regression tests pass verifying colour preservation
- All existing tests continue to pass
</success_criteria>

<output>
After completion, create `.planning/quick/003-fix-png-colour-difference-vs-svg-pdf-sha/003-SUMMARY.md`
</output>
