# Deploying SecureCloud to Netlify

This project is fully pre-configured for seamless, zero-config deployment to [Netlify](https://www.netlify.com/).

---

## 🚀 Deployment Methods

### Method 1: Connect via GitHub (Recommended & Automated)

1. **Push your code to GitHub** (if not already pushed):
   ```bash
   git add .
   git commit -m "Configure Netlify deployment"
   git push origin main
   ```
2. Log into [Netlify](https://app.netlify.com/).
3. Click **"Add new site"** → **"Import an existing project"**.
4. Select **GitHub** and pick your `secure-cloud` repository.
5. Netlify will **automatically detect** the root `netlify.toml`:
   - **Publish directory:** `securecloud/frontend`
   - **Build command:** *(leave empty)*
6. Click **"Deploy site"**! Your site will be live within seconds.

---

### Method 2: Instant Drag-and-Drop (Netlify Drop)

If you don't want to connect Git:
1. Go to [app.netlify.com/drop](https://app.netlify.com/drop).
2. Drag and drop the `securecloud/frontend` folder directly from your file explorer into the browser.
3. Done! Netlify publishes your site immediately with a free HTTPS URL.

---

### Method 3: Netlify CLI

If you prefer deploying from your terminal:
```powershell
# Run one-time deploy (preview)
npx netlify-cli deploy --dir=securecloud/frontend

# Deploy straight to production
npx netlify-cli deploy --dir=securecloud/frontend --prod
```

---

## ⚡ Connecting Your FastAPI Backend

Netlify hosts your static client application (`HTML`, `CSS`, `JS`, and architecture specifications). The Python FastAPI backend handles AES-256 encryption, local key storage, and AWS S3 communication.

### Where can the backend run?
1. **Localhost (Development):**
   Run `uvicorn backend.main:app --reload` on your machine.
   When testing locally (`http://localhost...`), the frontend automatically connects to `http://127.0.0.1:8000`.
2. **Free Cloud Host (Render / Railway / Fly.io / AWS App Runner):**
   Deploy `securecloud/backend` to any host that supports Python and HTTPS.

### Setting Your Backend API URL
You can set your backend URL through any of these 4 flexible ways:

1. **Through the UI (Easiest):**
   - Click the **API Status Badge** or the **Settings (gear)** icon in the top navigation bar.
   - Enter your deployed backend URL (e.g. `https://your-api.onrender.com`).
   - Click **Connect**. It tests the health check and remembers your setting in `localStorage`!
2. **Via URL Parameter:**
   - Share a demo link with the backend attached: `https://your-site.netlify.app/?api=https://your-api.onrender.com`
3. **In `config.js`:**
   - Open `securecloud/frontend/config.js` and set `API_BASE_URL: "https://your-api.onrender.com"`.
4. **Via Netlify Redirect Proxy:**
   - In `netlify.toml`, uncomment the `[[redirects]]` section to proxy `/api/*` requests directly to your backend.

> [!IMPORTANT]
> **HTTPS Mixed Content Rule:**
> Netlify serves all sites over **HTTPS**. Browsers block requests from an `https://` site to an insecure `http://` backend. Make sure your production backend URL uses `https://`.

---

## 📁 Included Pages
- **Interactive Vault Dashboard:** `/` (`index.html`)
- **System Architecture & Specifications:** `/portfolio` (`portfolio/index.html`)
