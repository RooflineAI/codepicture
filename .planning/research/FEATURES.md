# Feature Research

**Domain:** Code Screenshot / Code Image Generation CLI Tools
**Researched:** 2026-01-28
**Confidence:** HIGH (multiple primary sources verified)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Syntax highlighting | Every competitor has it. Code without highlighting looks unprofessional | MEDIUM | Requires Pygments integration. 300+ languages expected |
| Multiple output formats (PNG, SVG) | Carbon/ray.so/Silicon all support both. PNG for sharing, SVG for vector quality | MEDIUM | Cairo can do both natively |
| Window chrome (macOS-style title bar) | The defining visual of "pretty code screenshots" - red/yellow/green buttons | LOW | Simple shape rendering |
| Configurable background color | Users expect to match their brand/theme | LOW | Single color parameter |
| Padding control | Cramped code looks bad. Users need breathing room | LOW | Padding parameter on all sides |
| Drop shadow | Adds depth and polish. Standard in Carbon, ray.so, Silicon | MEDIUM | Shadow blur radius, offset, color |
| Line numbers (toggleable) | Many use cases need them, some don't. Must be optional | LOW | Simple line numbering logic |
| Font selection | Monospace font choice is personal. Fira Code, JetBrains Mono popular | LOW | Cairo font selection |
| Theme selection | Users expect Dracula, Monokai, GitHub Dark, etc. | LOW | Pygments has 30+ themes built-in |
| File input | Basic CLI requirement - read code from file | LOW | Standard file I/O |
| stdin input | Pipeline usage: `cat file.py \| codepicture -o out.png` | LOW | Standard stdin reading |
| Language auto-detection | Carbon/ray.so do this. Users expect it from file extension | LOW | Map extensions to Pygments lexers |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Custom lexers (MLIR)** | Silicon/Carbon don't support MLIR. Unique for ML/compiler community | MEDIUM | Pygments custom lexer API. Already planned |
| **PDF output** | Neither Silicon nor Carbon offer PDF. Useful for docs/papers | LOW | Cairo has PDF surface support |
| **Clipboard input/output** | Silicon has this. Carbon-now-cli has it. Very convenient for workflows | MEDIUM | Platform-specific: pbcopy/xclip |
| **Gradient backgrounds** | ray.so's signature look. Carbon has it. More visual appeal | MEDIUM | Cairo gradient patterns |
| **Line highlighting** | Emphasize specific lines (e.g., `--highlight 3-5`). Silicon has this | MEDIUM | Requires background color per line |
| **Window title** | Custom title in the macOS-style bar. Carbon/Silicon support this | LOW | Text rendering in title bar area |
| **Configurable window controls** | None/macOS/Windows style. Silicon has `--no-window-controls` | LOW | Optional render of buttons |
| **Rounded corners** | Modern, polished look. Many tools have this | LOW | Border radius on container |
| **Font ligatures** | Fira Code users expect `=>` to render as arrow. Differentiates quality | HIGH | HarfBuzz integration needed |
| **First line number offset** | Start numbering at line 100, not 1. Useful for excerpts | LOW | Simple offset parameter |
| **Tab width configuration** | Different projects use 2, 4, or 8 spaces | LOW | Tab expansion setting |
| **Configuration file** | Silicon has `--config-file`. Saves retyping options | LOW | TOML/JSON config loader |
| **Presets** | carbon-now-cli has named presets. Quick switching between styles | MEDIUM | Named config bundles |
| **Image background** | Custom image behind code instead of solid/gradient | MEDIUM | Cairo image surface compositing |
| **2x/retina output** | High-DPI screens need 2x images. carbon-now-cli has this | LOW | Scale factor multiplier |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-time web preview** | "I want to see changes live" | Scope creep into web app. Carbon/ray.so already exist. CLI is the differentiator | Let users iterate with fast CLI; provide `--open` to open result in browser/viewer |
| **Multi-file/diff views** | "Show before/after" | Major complexity increase. Snappify's territory. Muddies core value prop | Let users compose images externally. Or add as v2+ feature |
| **Animation/video output** | "Show code typing effect" | Massive scope increase. Snappify charges $5-32/mo for this | Stay in static image lane. Users can use other tools for animation |
| **Embedding/iframes** | "I want to embed in my blog" | Requires hosting infrastructure. Carbon does this well | Generate images. Users embed images |
| **API/web service** | "I want to call this from my app" | Deployment complexity. Maintenance burden. Out of scope for CLI tool | Provide as library with Python API for programmatic use |
| **Editor integrations** | "I want a VS Code extension" | Maintenance burden. Many editors to support. Extensions are separate projects | Document how to use CLI from editor terminal. Let community build extensions |
| **Account/cloud save** | "Save my snippets online" | Infrastructure, auth, storage costs. Snappify's business model | Local config files. No cloud dependency |
| **AI-generated explanations** | "Add AI annotations to my code" | Requires LLM API. Scope creep. Snappify has this | Out of scope. Users annotate manually |
| **Accessibility alt-text generation** | "Generate alt text for the image" | Nice idea but code-in-images is inherently accessibility-hostile | Document that code screenshots shouldn't be used for primary code sharing. Encourage text alternatives |

## Feature Dependencies

```
[Syntax Highlighting]
    |
    +---> [Theme Selection] (themes define highlighting colors)
    +---> [Line Highlighting] (needs to know syntax boundaries)
    +---> [Language Auto-Detection] (selects correct lexer)
    +---> [Custom Lexers] (extends Pygments)

[Window Chrome]
    |
    +---> [Window Title] (rendered in chrome area)
    +---> [Window Controls] (macOS buttons in chrome)
    +---> [Configurable Window Style] (none/macOS/Windows)

[Output Rendering (Cairo/Pango)]
    |
    +---> [PNG Output]
    +---> [SVG Output]
    +---> [PDF Output]
    +---> [Drop Shadow] (image compositing)
    +---> [Gradient Backgrounds] (pattern fills)
    +---> [Rounded Corners] (path clipping)
    +---> [Font Ligatures] (HarfBuzz via Pango)
    +---> [2x/Retina Output] (scale factor)

[Input Handling]
    |
    +---> [File Input]
    +---> [stdin Input]
    +---> [Clipboard Input] (platform-specific)

[Configuration]
    |
    +---> [CLI Arguments]
    +---> [Config File] (persistent defaults)
    +---> [Presets] (named config bundles)
```

### Dependency Notes

- **Syntax Highlighting is foundational:** Everything visual about the code depends on the lexer/highlighter working correctly first
- **Cairo/Pango enables all output formats:** PNG, SVG, and PDF all come from Cairo. Invest in the rendering pipeline once.
- **Clipboard is platform-specific:** macOS (pbcopy/pbpaste), Linux (xclip/xsel), Windows (clip). Each needs separate handling.
- **Font ligatures require HarfBuzz:** Pango uses HarfBuzz for text shaping. Ligature support depends on font + HarfBuzz.
- **Config files enable presets:** Once you have config file support, presets are just named config bundles.

## MVP Definition

### Launch With (v1)

Minimum viable product - what's needed to validate the concept.

- [x] Syntax highlighting with Pygments - essential, core value
- [x] PNG output - most common use case
- [x] SVG output - vector quality for docs
- [x] macOS window chrome - the signature "pretty code" look
- [x] Configurable background color - basic customization
- [x] Padding control - professional appearance
- [x] Drop shadow - depth and polish
- [x] Line numbers (toggleable) - common need
- [x] Font selection - monospace font choice
- [x] Theme selection (Pygments built-in) - Dracula, Monokai, etc.
- [x] File input - basic file reading
- [x] stdin input - pipeline support
- [x] Language auto-detection - convenience from file extension
- [x] MLIR custom lexer - the differentiator for ML/compiler users

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] PDF output - when users ask for it, add quickly (Cairo supports it)
- [ ] Clipboard input/output - when users report workflow friction
- [ ] Gradient backgrounds - when users want more visual appeal
- [ ] Line highlighting - when users ask for emphasis on specific lines
- [ ] Window title - when users want custom titles
- [ ] Rounded corners - when users want modern look
- [ ] Configuration file - when users complain about retyping options
- [ ] 2x/retina output - when users report fuzzy images on HiDPI

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Font ligatures - HIGH complexity, HarfBuzz integration needed
- [ ] Presets system - only after config files prove useful
- [ ] Image backgrounds - nice-to-have, not essential
- [ ] Additional custom lexers - based on user demand
- [ ] Configurable window control styles - low priority customization

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Syntax highlighting | HIGH | MEDIUM | P1 |
| PNG/SVG output | HIGH | MEDIUM | P1 |
| macOS window chrome | HIGH | LOW | P1 |
| Drop shadow | MEDIUM | MEDIUM | P1 |
| Theme selection | HIGH | LOW | P1 |
| Line numbers | MEDIUM | LOW | P1 |
| stdin input | MEDIUM | LOW | P1 |
| MLIR lexer | HIGH (niche) | MEDIUM | P1 |
| PDF output | MEDIUM | LOW | P2 |
| Clipboard I/O | MEDIUM | MEDIUM | P2 |
| Gradient backgrounds | MEDIUM | MEDIUM | P2 |
| Line highlighting | MEDIUM | MEDIUM | P2 |
| Config file | MEDIUM | LOW | P2 |
| 2x/retina | LOW | LOW | P2 |
| Font ligatures | MEDIUM | HIGH | P3 |
| Presets | LOW | MEDIUM | P3 |
| Image backgrounds | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Carbon | ray.so | Silicon | codepicture (Planned) |
|---------|--------|--------|---------|----------------------|
| Web-based | Yes | Yes | No | No |
| CLI | Via carbon-now-cli | No | Yes | Yes |
| Offline | No | No | Yes | Yes |
| PNG export | Yes | Yes | Yes | Yes |
| SVG export | Yes | Yes | Yes | Yes |
| PDF export | No | No | No | **Yes** |
| macOS chrome | Yes | Yes | Yes | Yes |
| Themes | Dozens | Limited | Many (syntect) | Many (Pygments) |
| Custom lexers | No | No | Via syntect/bat | **Yes (MLIR focus)** |
| Gradient BG | Yes | Yes | No | Planned |
| Line highlight | Yes | No | Yes | Planned |
| Clipboard | Yes | No | Yes | Planned |
| Config file | No | No | Yes | Planned |
| Free | Yes | Yes | Yes | Yes |
| Open source | Yes | Partial | Yes | Yes |
| Speed | Slow (browser) | Medium (web) | Fast (native) | Fast (native) |

### codepicture's Competitive Position

**Unique advantages:**
1. **MLIR support** - No competitor supports MLIR. Immediate value for ML/compiler community.
2. **PDF output** - Unique among competitors. Valuable for academic papers, documentation.
3. **Python ecosystem** - Easier to extend than Rust (Silicon). Familiar to ML/data science users.
4. **Offline + Fast** - Like Silicon, unlike Carbon/ray.so.

**Parity with leaders:**
- Feature-complete with Silicon for core functionality
- Visual quality matching Carbon/ray.so

**Deliberate gaps:**
- No web interface (Carbon/ray.so handle that)
- No animation (Snappify handles that)
- No cloud features (simplicity is a feature)

## Sources

**Primary (HIGH confidence):**
- [Carbon GitHub](https://github.com/carbon-app/carbon) - Feature list, export formats
- [Silicon GitHub](https://github.com/Aloxaf/silicon) - CLI options, syntect integration
- [carbon-now-cli GitHub](https://github.com/mixn/carbon-now-cli) - CLI configuration options
- [syntect documentation](https://github.com/trishume/syntect) - Rust syntax highlighting capabilities

**Secondary (MEDIUM confidence):**
- [Snappify comparison article](https://snappify.com/blog/best-code-to-image-converters) - Feature matrix across tools
- [ray.so](https://www.ray.so/) - Feature observation
- [DEV.to accessibility article](https://dev.to/savvasstephnds/the-problem-with-code-screenshots-and-how-to-fix-it-2ka0) - Anti-pattern justification

**Competitor analysis:**
- [Snappify blog](https://snappify.com/blog/best-ray-so-alternatives) - Pricing and feature comparison
- Web search results 2026-01-28 - Multiple tool comparisons

---
*Feature research for: Code Screenshot CLI Tools*
*Researched: 2026-01-28*
