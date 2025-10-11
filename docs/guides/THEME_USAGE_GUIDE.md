# 🌈 Theme Usage Guide - VÉRTICE Platform

**Version**: 1.0  
**Last Updated**: 2025-01-11  
**Themes Available**: 7 (3 categories)

---

## 🎨 Overview

VÉRTICE features a **dual-identity theme system**: cyberpunk hacker aesthetics + professional enterprise polish. One codebase, infinite possibilities.

---

## 📋 Available Themes

### 🔥 Hacker Themes (Cyberpunk Vibes)

#### 1. Matrix Green
```javascript
id: 'matrix-green'
name: 'Matrix Green'
category: 'hacker'
```
- **Identity**: Classic hacker aesthetic
- **Primary Color**: Neon green (#00ff88)
- **Best For**: Terminal work, coding, late-night ops
- **Mood**: Cyberpunk, underground, retro-futuristic

#### 2. Cyber Blue (Default/Flagship)
```javascript
id: 'cyber-blue'
name: 'Cyber Blue'
category: 'hacker'
```
- **Identity**: Electric blue hacker
- **Primary Color**: Electric blue (#00d4ff)
- **Best For**: General use, balanced visibility
- **Mood**: High-tech, energetic, modern

#### 3. Purple Haze
```javascript
id: 'purple-haze'
name: 'Purple Haze'
category: 'hacker'
```
- **Identity**: Purple team specialist
- **Primary Color**: Mystic purple (#b794f6)
- **Best For**: Purple team operations, creative work
- **Mood**: Mysterious, creative, unconventional

---

### 💼 Enterprise Themes (Professional Polish)

#### 4. Windows 11
```javascript
id: 'windows11'
name: 'Windows 11'
category: 'enterprise'
```
- **Identity**: Corporate professional
- **Primary Color**: Microsoft Blue (#0078d4)
- **Best For**: Client presentations, executive demos, office environments
- **Mood**: Professional, trustworthy, clean
- **Features**:
  - Fluent Design shadows
  - Mica-style backgrounds
  - Subtle animations
  - High contrast for readability
  - System fonts (Segoe UI)

**Perfect for:**
- 📊 Board presentations
- 🤝 Client meetings
- 💼 Corporate environments
- 📈 Executive dashboards

---

### ⚠️ Operational Themes (Mission Critical)

#### 5. Amber Alert
```javascript
id: 'amber-alert'
name: 'Amber Alert'
category: 'operational'
```
- **Identity**: Warning state
- **Primary Color**: Amber (#ffaa00)
- **Best For**: Warning scenarios, moderate threat levels
- **Mood**: Alert, cautious, heightened awareness

#### 6. Red Alert
```javascript
id: 'red-alert'
name: 'Red Alert'
category: 'operational'
```
- **Identity**: Critical operations
- **Primary Color**: Danger red (#ff0040)
- **Best For**: Critical incidents, high-threat situations
- **Mood**: Urgent, critical, emergency

#### 7. Stealth Mode
```javascript
id: 'stealth-mode'
name: 'Stealth Mode'
category: 'operational'
```
- **Identity**: Dark operations
- **Primary Color**: Subtle gray (#4a5568)
- **Best For**: Covert ops, minimal visibility, battery saving
- **Mood**: Stealthy, minimal, focused

---

## 🔄 Switching Themes

### Via UI (Recommended)

1. **Click theme selector** (icon in header/sidebar)
2. **Browse by category**:
   - 🔥 Hacker Themes
   - 💼 Enterprise Themes
   - ⚠️ Operational Themes
3. **Click theme card** → instant switch
4. **Theme persists** across sessions (localStorage)

### Via Code (Programmatic)

```javascript
import { useTheme } from '@/contexts/ThemeContext';

function MyComponent() {
  const { theme, setTheme } = useTheme();
  
  // Get current theme
  console.log(theme); // 'cyber-blue'
  
  // Switch theme
  setTheme('windows11');
  
  // Get themes by category
  const { getThemesByCategory } = useTheme();
  const hackerThemes = getThemesByCategory('hacker');
}
```

### Via URL Parameter

```
http://localhost:3000/?theme=windows11
```

Useful for:
- Sharing specific theme links
- Demo/presentation modes
- Testing themes

---

## 🎯 Theme Selection Guide

### Choose Based On:

#### 1. Audience
```
Developers/Hackers     → Matrix Green, Cyber Blue, Purple Haze
Executives/Clients     → Windows 11
Security Operations    → Red Alert, Amber Alert
Covert Operations      → Stealth Mode
```

#### 2. Time of Day
```
Morning (bright office) → Windows 11
Evening (dim lighting)  → Cyber Blue, Matrix Green
Night (dark room)       → Stealth Mode, Purple Haze
24/7 Ops (SOC)          → Red Alert, Amber Alert
```

#### 3. Task Type
```
Penetration Testing    → Purple Haze, Cyber Blue
Incident Response      → Red Alert
Threat Hunting         → Stealth Mode, Matrix Green
Client Presentations   → Windows 11
Monitoring Dashboards  → Amber Alert, Red Alert
```

#### 4. Environment
```
Corporate Office       → Windows 11
Home Office            → Any hacker theme
Security Operations    → Operational themes
Public Demo            → Windows 11 (safe bet)
Conference Booth       → Cyber Blue (eye-catching)
```

---

## 🎨 Theme Characteristics

### Color Psychology

| Theme | Primary Emotion | Secondary Emotion | Use Case |
|-------|----------------|-------------------|----------|
| Matrix Green | Focused | Nostalgic | Deep work, coding |
| Cyber Blue | Energetic | Modern | General use |
| Purple Haze | Creative | Mysterious | Purple team ops |
| Windows 11 | Professional | Trustworthy | Business settings |
| Amber Alert | Cautious | Alert | Warning states |
| Red Alert | Urgent | Critical | Emergencies |
| Stealth Mode | Focused | Stealthy | Covert work |

### Contrast Levels

```
High Contrast (Best Readability):
- Windows 11 (light bg, dark text)
- Red Alert (high visibility)

Medium Contrast:
- Cyber Blue
- Matrix Green
- Amber Alert

Low Contrast (Subtle):
- Stealth Mode
- Purple Haze
```

### Animation Intensity

```
Minimal (Professional):
- Windows 11

Moderate (Balanced):
- Cyber Blue
- Stealth Mode

High (Cyberpunk):
- Matrix Green
- Purple Haze
- Red Alert
```

---

## 🔧 Theme Customization (Future)

### Coming Soon

- [ ] **Dark/Light mode toggle** per theme
- [ ] **User custom themes** (theme builder UI)
- [ ] **Import/Export** theme configs
- [ ] **Scheduled themes** (auto-switch at night)
- [ ] **Per-dashboard themes** (different theme per page)

### Current Limitations

- Themes apply globally (not per-dashboard yet)
- No real-time preview (must switch to see)
- Limited to 7 predefined themes

---

## 🎓 Best Practices

### DO ✅

1. **Match theme to audience**
   ```
   Client demo? → Windows 11
   Team standup? → Cyber Blue
   ```

2. **Consider lighting conditions**
   ```
   Bright office? → Windows 11
   Dark room? → Stealth Mode
   ```

3. **Use operational themes purposefully**
   ```
   Normal ops → Default (Cyber Blue)
   Warning state → Amber Alert
   Critical incident → Red Alert
   ```

4. **Respect theme persistence**
   ```javascript
   // Theme saves automatically
   setTheme('windows11');
   // Will persist on reload
   ```

### DON'T ❌

1. **Don't use Red Alert for normal ops**
   - Red Alert = actual emergencies only
   - Causes alert fatigue if overused

2. **Don't switch themes mid-presentation**
   - Jarring for audience
   - Pick one and stick with it

3. **Don't use hacker themes for client demos** (unless they're hackers!)
   - Matrix Green may intimidate non-technical stakeholders
   - Windows 11 is safer for corporate settings

4. **Don't forget about accessibility**
   - Some users may need high contrast
   - Windows 11 best for low vision
   - Red Alert may be problematic for colorblind users

---

## 🌐 Theme Compatibility

### Browser Support

| Browser | Support | Notes |
|---------|---------|-------|
| Chrome 90+ | ✅ Full | CSS variables, smooth transitions |
| Firefox 88+ | ✅ Full | All features work |
| Safari 14+ | ✅ Full | Webkit prefix for some shadows |
| Edge 90+ | ✅ Full | Native support |
| Opera 76+ | ✅ Full | Chromium-based |

### Device Support

```
Desktop    ✅ Full support
Laptop     ✅ Full support
Tablet     ✅ Full support (responsive)
Mobile     ✅ Full support (touch-friendly)
```

### Display Modes

```
Light Room     → Windows 11 (best)
Dark Room      → Cyber Blue, Stealth Mode
Bright Sunlight → Windows 11 (highest contrast)
Projector      → Windows 11, Red Alert (high visibility)
Multi-Monitor  → Any theme (scales well)
```

---

## 🚀 Advanced Usage

### Theme Context API

```javascript
import { useTheme } from '@/contexts/ThemeContext';

function AdvancedComponent() {
  const {
    theme,              // Current theme ID
    setTheme,           // Switch theme function
    availableThemes,    // All themes array
    getThemesByCategory // Filter by category
  } = useTheme();
  
  // Get current theme metadata
  const currentTheme = availableThemes.find(t => t.id === theme);
  console.log(currentTheme.name);     // 'Cyber Blue'
  console.log(currentTheme.category);  // 'hacker'
  
  // Get all enterprise themes
  const enterpriseThemes = getThemesByCategory('enterprise');
  
  return (
    <div>
      <p>Current: {currentTheme.name}</p>
      <button onClick={() => setTheme('windows11')}>
        Switch to Enterprise
      </button>
    </div>
  );
}
```

### Reading Theme in CSS

```css
/* Theme-specific overrides */
[data-theme="windows11"] .my-component {
  /* Only applied when Windows 11 theme active */
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

[data-theme="red-alert"] .alert-banner {
  /* Pulse animation only in Red Alert */
  animation: pulse 2s infinite;
}
```

### Theme Detection in JS

```javascript
// Get current theme from DOM
const currentTheme = document.documentElement.getAttribute('data-theme');

// Listen for theme changes
const observer = new MutationObserver((mutations) => {
  mutations.forEach((mutation) => {
    if (mutation.attributeName === 'data-theme') {
      const newTheme = document.documentElement.getAttribute('data-theme');
      console.log('Theme changed to:', newTheme);
    }
  });
});

observer.observe(document.documentElement, {
  attributes: true,
  attributeFilter: ['data-theme']
});
```

---

## 📊 Theme Analytics (Ideas)

Track theme usage to understand user preferences:

```javascript
// Log theme switches
analytics.track('Theme Changed', {
  from: 'cyber-blue',
  to: 'windows11',
  timestamp: Date.now()
});

// Aggregate data
// - Most popular theme?
// - Time of day preferences?
// - User segments (hacker vs enterprise)?
```

---

## 🎬 Demo Scenarios

### Scenario 1: Client Presentation
```
1. Start with Windows 11 (professional)
2. Show defensive dashboard
3. Demonstrate threat detection
4. Keep in Windows 11 throughout
5. Mention other themes exist for operators
```

### Scenario 2: Security Team Training
```
1. Start with Cyber Blue (comfortable)
2. Switch to Matrix Green for terminal demo
3. Use Purple Haze for purple team section
4. Show Red Alert during incident simulation
5. End with Stealth Mode for covert ops demo
```

### Scenario 3: Live SOC Monitoring
```
Normal State: Cyber Blue
Warning Level: Amber Alert (automatic switch)
Critical Incident: Red Alert (automatic switch)
Resolved: Return to Cyber Blue
```

---

## 🔐 Security Note

**Themes are cosmetic only** - they do NOT affect:
- Security posture
- Data access
- API responses
- Backend behavior
- Authentication/authorization

All themes have **equal security**. Choose based on UX, not security.

---

## 📚 Additional Resources

- **Design Tokens Guide**: `docs/guides/DESIGN_TOKENS_GUIDE.md`
- **Migration Guide**: `docs/guides/THEME_MIGRATION_GUIDE.md`
- **Theme System Architecture**: `docs/architecture/frontend/theme-system-blueprint.md`
- **Component Examples**: `frontend/src/themes/`

---

**Version**: 1.0  
**Status**: Production Ready  
**Maintainer**: MAXIMUS Team  
**Glory**: YHWH through Christ 🙏
