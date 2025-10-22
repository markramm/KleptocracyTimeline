# Setting Up Your Own Timeline Fork with GitHub Pages

This guide will help you fork the Kleptocracy Timeline and deploy your own version on GitHub Pages.

## Prerequisites

- GitHub account
- Basic familiarity with git
- (Optional) Node.js 18+ and npm for local development

## Quick Setup (5 minutes)

### 1. Fork the Repository

1. Visit https://github.com/markramm/KleptocracyTimeline
2. Click the **Fork** button in the top right
3. Choose your account/organization
4. Wait for the fork to complete

### 2. Enable GitHub Pages

1. In your forked repository, go to **Settings** → **Pages**
2. Under "Build and deployment":
   - **Source**: Select "GitHub Actions"
3. Click **Save**

### 3. Update Configuration

You need to update a few files to point to your fork:

#### A. Update `timeline/viewer/package.json`

Find and change the `homepage` field:

```json
{
  "homepage": "https://YOUR-USERNAME.github.io/KleptocracyTimeline"
}
```

Replace `YOUR-USERNAME` with your GitHub username.

#### B. Update `timeline/viewer/src/utils/githubUtils.js`

Change line 3:

```javascript
const GITHUB_REPO = 'https://github.com/YOUR-USERNAME/KleptocracyTimeline';
```

#### C. Update `timeline/viewer/src/config.js` (Optional)

Line 83 - if you renamed your fork:

```javascript
export const RAW_DATA_URL = `https://raw.githubusercontent.com/YOUR-USERNAME/YOUR-REPO-NAME/main/timeline/data`;
```

### 4. Commit and Push Changes

```bash
git add timeline/viewer/package.json timeline/viewer/src/utils/githubUtils.js timeline/viewer/src/config.js
git commit -m "Configure for my GitHub Pages deployment"
git push origin main
```

### 5. Wait for Deployment

1. Go to **Actions** tab in your repository
2. Watch the "CI/CD Pipeline" workflow run
3. Once complete (✓ green checkmark), visit:
   ```
   https://YOUR-USERNAME.github.io/KleptocracyTimeline
   ```

🎉 **Your timeline is now live!**

---

## Advanced Configuration

### Custom Domain (Optional)

If you want to use your own domain (e.g., `timeline.yoursite.com`):

1. In **Settings** → **Pages** → **Custom domain**
2. Enter your domain name
3. Add a CNAME record in your DNS settings:
   ```
   CNAME timeline YOUR-USERNAME.github.io
   ```
4. Wait for DNS propagation (5-60 minutes)
5. Enable "Enforce HTTPS" once DNS is active

### Update Repository Name

If you renamed your fork:

1. **Settings** → **General** → **Repository name**
2. Update the URLs in the configuration files above
3. Update the `homepage` in `package.json` to match new name

### Environment Variables

For advanced configuration, you can set environment variables:

Create `.env.production`:

```bash
REACT_APP_GITHUB_REPO=YOUR-USERNAME/YOUR-REPO-NAME
REACT_APP_GITHUB_PAGES_URL=https://YOUR-USERNAME.github.io/YOUR-REPO-NAME
```

---

## Local Development

To develop and test locally before deploying:

### 1. Clone Your Fork

```bash
git clone https://github.com/YOUR-USERNAME/KleptocracyTimeline.git
cd KleptocracyTimeline
```

### 2. Install Dependencies

```bash
# Install viewer dependencies
cd timeline/viewer
npm install
```

### 3. Run Development Server

```bash
npm start
```

This opens the viewer at http://localhost:3000

### 4. Build for Production

Test the production build locally:

```bash
npm run build:gh-pages
```

This creates an optimized build in `timeline/viewer/build/`

You can test it with:

```bash
# Serve the build directory
npx serve -s build
```

---

## Adding New Events

### Method 1: GitHub Web Interface (Easiest)

1. Navigate to `timeline/data/events/` in your fork
2. Click **Add file** → **Create new file**
3. Name it: `YYYY-MM-DD--descriptive-slug.md`
4. Use the template from [CONTRIBUTING.md](CONTRIBUTING.md)
5. Commit directly to main branch
6. GitHub Actions will automatically rebuild and deploy

### Method 2: Local Development

1. Create event file in `timeline/data/events/`
2. Follow format in [timeline/docs/EVENT_FORMAT.md](timeline/docs/EVENT_FORMAT.md)
3. Validate:
   ```bash
   python3 timeline/scripts/validate.py
   ```
4. Commit and push:
   ```bash
   git add timeline/data/events/YOUR-EVENT.md
   git commit -m "Add: YYYY-MM-DD event description"
   git push origin main
   ```

### Method 3: Pull Request (Collaborative)

1. Create a new branch:
   ```bash
   git checkout -b add-event-YYYY-MM-DD
   ```
2. Add your event file
3. Push branch:
   ```bash
   git push origin add-event-YYYY-MM-DD
   ```
4. Create Pull Request on GitHub
5. Review and merge

---

## Troubleshooting

### Build Fails

**Check the Actions tab** for error details:

Common issues:
- Invalid event JSON/YAML → Fix event format
- Missing fields → Add required fields (date, title, importance)
- Duplicate event IDs → Use unique ID format `YYYY-MM-DD--slug`

### Page Shows 404

**Possible causes:**
1. GitHub Pages not enabled → Check Settings → Pages
2. Wrong homepage URL in package.json → Update to match your username
3. Build not completed → Wait for Actions workflow to finish

### Changes Not Showing

**Solutions:**
1. Hard refresh browser: Ctrl+F5 (Windows/Linux) or Cmd+Shift+R (Mac)
2. Wait 2-5 minutes for GitHub Pages cache to clear
3. Check Actions tab to confirm deployment succeeded

### Contribute Button Not Working

If the "Contribute" button creates issues on the wrong repository:

1. Update `timeline/viewer/src/utils/githubUtils.js` line 3
2. Make sure it points to YOUR fork, not the original

---

## Customization Ideas

### Change Color Scheme

Edit `timeline/viewer/src/components/LandingPage.css`:

```css
.landing-header h1 {
  background: linear-gradient(135deg, #YOUR-COLOR-1, #YOUR-COLOR-2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Update Landing Page

Edit `timeline/viewer/src/components/LandingPage.js`:
- Change tagline
- Update mission statement
- Modify key findings
- Add your own branding

### Add Analytics

Uncomment analytics code in `timeline/viewer/public/index.html`:

```html
<!-- Plausible Analytics -->
<script defer data-domain="YOUR-DOMAIN.github.io" src="https://plausible.io/js/script.js"></script>
```

Or use GoatCounter (free):

```html
<script data-goatcounter="https://YOUR-SITE.goatcounter.com/count"
        async src="//gc.zgo.at/count.js"></script>
```

---

## Keeping Your Fork Updated

To sync with upstream changes:

### One-Time Setup

```bash
git remote add upstream https://github.com/markramm/KleptocracyTimeline.git
```

### Regular Updates

```bash
# Fetch upstream changes
git fetch upstream

# Merge into your main branch
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

### Handle Conflicts

If there are conflicts in configuration files:

```bash
git merge upstream/main
# Fix conflicts in your editor
git add <conflicted-files>
git commit
git push origin main
```

**Tip:** Keep your customizations in separate commits so they're easier to reapply after merges.

---

## Deployment Checklist

Before going live:

- [ ] Updated `homepage` in package.json
- [ ] Updated `GITHUB_REPO` in githubUtils.js
- [ ] Enabled GitHub Pages in repository settings
- [ ] Tested build locally (`npm run build:gh-pages`)
- [ ] Verified all links work
- [ ] Checked landing page stats load correctly
- [ ] Tested contribute button
- [ ] Added at least one custom event
- [ ] (Optional) Set up custom domain
- [ ] (Optional) Added analytics

---

## Community & Support

- **Original Repository**: https://github.com/markramm/KleptocracyTimeline
- **Documentation**: See [timeline/docs/](timeline/docs/)
- **Contributing Guide**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Discussions**: GitHub Discussions tab

---

## License

- **Data**: Creative Commons Attribution-ShareAlike 4.0 (CC BY-SA 4.0)
- **Code**: MIT License

When forking, you must:
- Maintain attribution to original project
- Share derivative data under same license (CC BY-SA 4.0)
- Include MIT license for code

See [LICENSE-DATA](LICENSE-DATA) and [LICENSE-MIT](LICENSE-MIT) for full terms.

---

## What Next?

1. ✅ Get your fork deployed on GitHub Pages
2. Add your own custom events relevant to your region/topic
3. Customize the landing page for your audience
4. Share your timeline!
5. Consider contributing events back to the main repository

**Happy documenting!** 📊✨
