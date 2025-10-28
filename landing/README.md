# Vértice-MAXIMUS Landing Page

> Production-ready landing page para lançamento open-source do Vértice-MAXIMUS.

[![Built with Astro](https://img.shields.io/badge/Built%20with-Astro-FF5D01?logo=astro)](https://astro.build)
[![React](https://img.shields.io/badge/React-19.2-61DAFB?logo=react)](https://react.dev)
[![Firebase](https://img.shields.io/badge/Deployed%20on-Firebase-FFCA28?logo=firebase)](https://firebase.google.com)

---

## 🎯 Overview

Landing page construída com **Padrão Pagani**:
- ✅ Zero mocks, zero placeholders
- ✅ Production-ready desde o primeiro commit
- ✅ Build successful (~1.5s, 186KB bundle gzipped)
- ✅ SEO completo (structured data, OpenGraph)
- ✅ Lighthouse 100/100 target

### Tech Stack

- **Astro 5.x** - Static Site Generator
- **React 19** - Islands architecture
- **Tailwind CSS 4.x** - Styling
- **Firebase Hosting** - CDN global (FREE)

---

## 🚀 Quick Start

```bash
# Install
npm install

# Dev (http://localhost:4321)
npm run dev

# Build
npm run build

# Preview
npm run preview
```

---

## 🔥 Deploy Firebase

```bash
# Install Firebase CLI (se não tiver)
npm install -g firebase-tools

# Login
firebase login

# Deploy
npm run build
firebase deploy --only hosting
```

---

## 📐 Arquitetura

```
landing/
├── src/
│   ├── components/
│   │   ├── Hero/          # Hero + GitHub Stars API
│   │   ├── Features/      # Features grid (6 capabilities)
│   │   ├── GettingStarted/# Tabs (Docker/K8s/Manual)
│   │   └── Footer/        # Footer completo
│   ├── layouts/
│   │   └── BaseLayout.astro  # SEO, meta tags
│   ├── pages/
│   │   └── index.astro    # Página principal
│   └── styles/
│       ├── design-system.css   # Design tokens
│       └── code-highlight.css  # Syntax highlighting
├── firebase.json          # Firebase config
└── .firebaserc           # Project ID
```

---

## 📊 Build Stats

- **Client bundle:** 186.62 kB (58.53 kB gzipped)
- **Build time:** ~1.5s
- **Lighthouse score:** Target 100/100

---

## 🔍 Componentes

### ✅ Implementados

- **Hero Section** - Tagline, CTAs, GitHub Stars (API real)
- **Features Grid** - 6 capabilities, SVG icons
- **Getting Started** - Tabs, syntax highlighting, copy-to-clipboard
- **Footer** - Links, social, legal

### 🚧 Roadmap

- [ ] Architecture Diagram (Mermaid.js)
- [ ] Screenshots Carousel (5 dashboards)
- [ ] Community Section (GitHub stats)
- [ ] Sponsors Section (GitHub Sponsors, Patreon)

---

## 🐛 Troubleshooting

```bash
# Clear cache
rm -rf node_modules dist
npm install
npm run build
```

---

**Built with ❤️ by the Vértice Team**

**Status:** Production-Ready MVP ✅
