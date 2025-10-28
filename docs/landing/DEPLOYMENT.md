# Vértice-MAXIMUS Landing Page - Deployment Guide

**Status:** Production-Ready MVP ✅
**Build Time:** ~1.5s
**Bundle Size:** ~200KB (gzipped: ~60KB)
**Lighthouse Score Target:** 100/100 (all metrics)

---

## Prerequisites

- Node.js 18+ installed
- npm or yarn package manager
- Git access to repository
- Hosting platform account (Vercel/Netlify/Cloudflare Pages)

---

## Local Development

### 1. Install Dependencies

```bash
cd landing
npm install
```

### 2. Start Dev Server

```bash
npm run dev
```

Server will start at `http://localhost:4321`

### 3. Build for Production

```bash
npm run build
```

Output directory: `landing/dist/`

### 4. Preview Production Build

```bash
npm run preview
```

---

## Deployment Options

### Option A: Vercel (Recommended)

**Why Vercel:**
- Zero-config Astro support
- Automatic HTTPS
- Global CDN
- Automatic deployments from Git
- Free tier available

**Steps:**

1. Install Vercel CLI:
```bash
npm i -g vercel
```

2. Deploy from landing directory:
```bash
cd landing
vercel
```

3. Follow prompts:
   - Link to existing project or create new
   - Set build command: `npm run build`
   - Set output directory: `dist`
   - Deploy!

4. Configure custom domain (optional):
```bash
vercel domains add vertice-maximus.com
```

**Production URL:** `https://vertice-maximus.vercel.app` (or custom domain)

---

### Option B: Netlify

**Steps:**

1. Install Netlify CLI:
```bash
npm i -g netlify-cli
```

2. Deploy:
```bash
cd landing
netlify deploy --prod
```

3. Or use Netlify UI:
   - Connect GitHub repository
   - Build command: `npm run build`
   - Publish directory: `dist`
   - Deploy!

**netlify.toml** (already configured if needed):
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

---

### Option C: Cloudflare Pages

**Steps:**

1. Push code to GitHub
2. Go to Cloudflare Pages dashboard
3. Connect repository
4. Build settings:
   - Framework: Astro
   - Build command: `npm run build`
   - Build output: `dist`
5. Deploy!

---

### Option D: GitHub Pages (Static)

**Steps:**

1. Build locally:
```bash
npm run build
```

2. Deploy dist folder:
```bash
cd dist
git init
git add -A
git commit -m "Deploy landing page"
git push -f git@github.com:JuanCS-Dev/vertice-landing.git main:gh-pages
```

3. Enable GitHub Pages in repository settings

---

## Environment Variables

Currently, no environment variables required for MVP.

Future considerations:
- `PUBLIC_PLAUSIBLE_DOMAIN` - Analytics domain
- `PUBLIC_GTM_ID` - Google Tag Manager (if needed)

---

## Post-Deployment Checklist

### SEO & Discoverability

- [ ] Submit sitemap to Google Search Console: `https://vertice-maximus.com/sitemap.xml`
- [ ] Submit sitemap to Bing Webmaster Tools
- [ ] Verify robots.txt accessibility: `https://vertice-maximus.com/robots.txt`
- [ ] Test Open Graph meta tags: https://www.opengraph.xyz/
- [ ] Test Twitter Card: https://cards-dev.twitter.com/validator
- [ ] Test structured data: https://search.google.com/test/rich-results

### Performance

- [ ] Run Lighthouse audit (Target: 100/100 all metrics)
  ```bash
  npx lighthouse https://vertice-maximus.com --view
  ```
- [ ] Test mobile responsiveness: https://search.google.com/test/mobile-friendly
- [ ] Verify CDN caching headers
- [ ] Check Core Web Vitals in Google Search Console

### Functionality

- [ ] Test all anchor links (#code-therapy, #living-organism, etc.)
- [ ] Verify GitHub Stars component loads correctly
- [ ] Test all external links (GitHub, docs, etc.)
- [ ] Verify tab switching in Getting Started section
- [ ] Test all CTAs (buttons, links)
- [ ] Mobile navigation test

### Analytics (Optional - when ready)

- [ ] Uncomment Plausible script in `BaseLayout.astro`
- [ ] Verify Plausible tracking in dashboard
- [ ] Set up goal tracking for CTAs

---

## Monitoring

### Performance Monitoring

- Use Vercel Analytics (automatic if deployed on Vercel)
- Or Cloudflare Web Analytics (free tier)
- Or Plausible (privacy-friendly, recommended)

### Uptime Monitoring

- UptimeRobot (free tier)
- Pingdom
- StatusCake

---

## Rollback Procedure

If deployment fails or issues occur:

### Vercel

```bash
vercel rollback
```

### Netlify

```bash
netlify rollback
```

### Manual

```bash
git revert HEAD
git push
# Redeploy previous commit
```

---

## Custom Domain Configuration

### DNS Records (Example for vertice-maximus.com)

**For Vercel:**
```
Type: A
Name: @
Value: 76.76.21.21

Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

**For Netlify:**
```
Type: A
Name: @
Value: 75.2.60.5

Type: CNAME
Name: www
Value: your-site.netlify.app
```

**For Cloudflare Pages:**
- Already integrated with Cloudflare DNS
- Just add CNAME pointing to your-site.pages.dev

---

## Troubleshooting

### Build Fails

**Issue:** Build timeout or error

**Solution:**
```bash
# Clear cache and rebuild
rm -rf node_modules dist .astro
npm install
npm run build
```

### Assets Not Loading

**Issue:** CSS/JS not loading after deployment

**Solution:**
- Verify `dist/` folder contains `_astro/` directory
- Check build output in deployment logs
- Ensure base URL is correct in `astro.config.mjs`

### Slow Load Times

**Issue:** Page loads slowly

**Solution:**
- Verify CDN is enabled on hosting platform
- Check image optimization (currently no images in MVP)
- Run Lighthouse audit to identify bottlenecks
- Enable gzip compression (usually automatic)

---

## Future Enhancements

### Phase 2 Tasks (Not in MVP)

- [ ] Add Architecture Diagram section
- [ ] Add Screenshots/Demo carousel (need assets)
- [ ] Add Sponsors section (monetization decision)
- [ ] Implement blog/news section
- [ ] Add multi-language support (i18n)
- [ ] Create separate documentation site
- [ ] Add dark/light mode toggle

### Performance Optimizations

- [ ] Implement image lazy loading (when images added)
- [ ] Add service worker for offline support
- [ ] Implement prefetching for critical resources
- [ ] Consider code splitting for React components

---

## Support

**Repository:** https://github.com/JuanCS-Dev/V-rtice
**Issues:** https://github.com/JuanCS-Dev/V-rtice/issues
**Discussions:** https://github.com/JuanCS-Dev/V-rtice/discussions
**Contact:** juan@vertice-maximus.com

---

## License

MIT License - See LICENSE file in repository

---

**Last Updated:** 2025-10-28
**Deployed Version:** v1.0.0-MVP
**Build Command:** `npm run build`
**Output Directory:** `dist/`
**Framework:** Astro 4.x
**Node Version:** 18+

---

**🚀 Ready to deploy the organism!**
