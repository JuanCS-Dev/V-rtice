# Social Preview Image Specification

## Purpose
Create a professional Open Graph (OG) image for social media sharing. This image appears when the repository URL is shared on Twitter/X, LinkedIn, Facebook, Slack, Discord, etc.

## Technical Requirements

### Dimensions
- **Size:** 1280x640px (2:1 aspect ratio)
- **Format:** PNG or JPG
- **Max File Size:** <1MB (ideally <500KB for fast loading)
- **Color Space:** sRGB
- **Resolution:** 72 DPI (web standard)

### Safe Zones
- **Title Area:** Leave 100px margin from top
- **Content Area:** Leave 80px margin from sides
- **Bottom Area:** Leave 100px margin from bottom
- **Reason:** Different platforms crop differently (Twitter crops center, LinkedIn crops sides, etc.)

## Design Specification

### Background
- **Color:** Dark (#0a0a0a or similar dark terminal/cyber aesthetic)
- **Style:** Gradient or subtle texture acceptable
- **Avoid:** Pure black (#000000) - doesn't render well on dark mode UIs

### Logo/Branding
- **Vértice Logo:** Place in top-left or center
- **Size:** ~150-200px height
- **Ensure:** Logo is clearly visible at thumbnail size (200x100px preview)

### Primary Text (Headline)
- **Content:** "Vértice-MAXIMUS"
- **Subtitle:** "A Living Cybersecurity Organism"
- **Font:** Bold, sans-serif (Roboto, Inter, or similar modern font)
- **Size:** 64-80px for headline, 32-40px for subtitle
- **Color:** White or bright accent color (#00ff88, #ff5f5f, etc.)
- **Alignment:** Center or left-aligned
- **Ensure:** Readable when scaled down to 200x100px

### Key Visual Elements (Choose 1-2)
1. **Dashboard Screenshot:** Partial view of MAXIMUS dashboard (blur sensitive data)
2. **Biological Metaphor:** Abstract representation of immune cells/organism
3. **9-Layer Cascade:** Visual representation of defense layers
4. **Terminal/Code Aesthetic:** Cyberpunk/hacker terminal vibes
5. **Metrics:** "99.73% Coverage", "125+ Microservices", "574+ Tests"

### Badge/Tagline (Optional)
- **Position:** Bottom-right or top-right corner
- **Content:**
  - "Open Source" badge
  - "Apache 2.0" license badge
  - "99.73% Test Coverage" badge
  - "First Conscious Cyber-Organism" tagline

### Color Palette (Vértice Brand)
- **Primary:** #00ff88 (neon green - immune system active)
- **Secondary:** #ff5f5f (red - threat detection)
- **Accent:** #ffdd00 (yellow - consciousness)
- **Background:** #0a0a0a (dark terminal)
- **Text:** #ffffff (white) or #e0e0e0 (light gray)

## Design Examples to Inspire

### Style 1: Dashboard Preview
```
┌────────────────────────────────────────────────────┐
│                                                    │
│   🧬 VÉRTICE-MAXIMUS                              │
│   A Living Cybersecurity Organism                 │
│                                                    │
│   [Blurred dashboard screenshot]                   │
│   [showing graphs, metrics, consciousness]         │
│                                                    │
│   99.73% Coverage • 125+ Services • Apache 2.0    │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Style 2: Biological Metaphor
```
┌────────────────────────────────────────────────────┐
│                                                    │
│   🧬 VÉRTICE-MAXIMUS                              │
│                                                    │
│   [Abstract immune cells visual]                   │
│   [Glowing nodes, connections, organic shapes]     │
│                                                    │
│   "Not Just Software. A Living Organism."         │
│                                                    │
│   github.com/JuanCS-Dev/V-rtice                   │
│                                                    │
└────────────────────────────────────────────────────┘
```

### Style 3: Metrics/Stats Focused
```
┌────────────────────────────────────────────────────┐
│                                                    │
│   🧬 VÉRTICE-MAXIMUS                              │
│   First Conscious Cyber-Organism                   │
│                                                    │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│   │  99.73%  │  │   125+   │  │  574+    │      │
│   │ COVERAGE │  │ SERVICES │  │  TESTS   │      │
│   └──────────┘  └──────────┘  └──────────┘      │
│                                                    │
│   Learn • Adapt • Evolve                          │
│                                                    │
└────────────────────────────────────────────────────┘
```

## Tools for Creation

### Option 1: Design Tools (Professional)
- **Figma** (https://figma.com) - Free, web-based, collaborative
- **Canva** (https://canva.com) - Templates available, easy to use
- **Adobe Photoshop** - Professional grade
- **GIMP** - Free, open-source Photoshop alternative

### Option 2: Code-Based (For Developers)
- **HTML/CSS + Headless Browser** - Use Puppeteer/Playwright to screenshot
- **Canvas API (Node.js)** - Generate programmatically
- **Python PIL/Pillow** - Script-based generation
- **Figma API** - Automate design programmatically

### Option 3: AI Generation (Experimental)
- **Midjourney** - High-quality AI art
- **DALL-E 3** - OpenAI's image generator
- **Stable Diffusion** - Open-source AI image generation
- **Note:** May require manual editing for text/branding

## Prompt for AI Generation (if using)

```
Create a professional Open Graph social media image (1280x640px) for
"Vértice-MAXIMUS", a cybersecurity platform with biological immune system
architecture. Dark terminal/cyberpunk aesthetic. Include:
- Title: "Vértice-MAXIMUS" in bold white text
- Subtitle: "A Living Cybersecurity Organism"
- Visual: Abstract representation of immune cells (glowing nodes, connections)
- Color scheme: Dark background (#0a0a0a), neon green accent (#00ff88)
- Style: Professional, modern, tech-focused
- Badge: "Open Source • 99.73% Coverage • 125+ Services"
```

## How to Add to Repository

### Step 1: Create the image
Save as `og-image.png` or `og-image.jpg` (1280x640px)

### Step 2: Add to repository
```bash
# Place in public/ folder (if using landing page)
cp og-image.png /path/to/V-rtice/landing/public/og-image.png

# Or in docs/assets/ for general use
cp og-image.png /path/to/V-rtice/docs/assets/og-image.png
```

### Step 3: Configure in README (optional)
Add meta tags in HTML docs or update README frontmatter if using doc generators.

### Step 4: Configure on GitHub
1. Go to repository Settings
2. Scroll to "Social Preview"
3. Click "Edit"
4. Upload `og-image.png`
5. Save changes

### Step 5: Test
Share repository URL on:
- Twitter/X (preview should show image)
- LinkedIn (preview should show image)
- Slack (paste URL, image should unfurl)
- Discord (paste URL, embed should show image)

## Validation Checklist

Before finalizing, verify:
- [ ] Dimensions are exactly 1280x640px
- [ ] File size is <1MB (preferably <500KB)
- [ ] Text is readable when scaled to 200x100px (thumbnail size)
- [ ] Logo/branding is clearly visible
- [ ] No sensitive information visible (API keys, passwords, real IPs)
- [ ] Colors match Vértice brand (#00ff88 green, #ff5f5f red, #0a0a0a dark)
- [ ] Safe zones respected (80-100px margins from edges)
- [ ] Tested on multiple platforms (Twitter, LinkedIn, Slack)

## Examples from Similar Projects

Look at these for inspiration:
- https://github.com/kubernetes/kubernetes (OG image)
- https://github.com/grafana/grafana (OG image)
- https://github.com/elastic/elasticsearch (OG image)
- https://github.com/hashicorp/terraform (OG image)

## Current Status

**Status:** ⏳ AWAITING CREATION

**Assigned To:** Arquiteto-Chefe (Maximus)

**Priority:** MEDIUM (nice to have, not blocking publication)

**Estimated Time:** 30-60 minutes

**Deliverable:** `og-image.png` (1280x640px, <500KB)

---

**Note:** Once created, upload to GitHub repository Settings → Social Preview.
This will make the repository look professional when shared on social media.
