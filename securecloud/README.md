# SecureCloud

**SecureCloud** is a sample project that demonstrates encrypted file storage on Amazon S3 (or a local in‑memory mock) via a FastAPI backend and a simple HTML/JS frontend.

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Using Amazon S3](#using-amazon-s3)
- [Running the Application](#running-the-application)
- [API Reference](#api-reference)
- [Frontend UI](#frontend-ui)
- [Testing](#testing)
- [Deployment Scripts](#deployment-scripts)
- [Portfolio Site](#portfolio-site)
- [Cost & Billing Guidance](#cost--billing-guidance)
- [Security Notes](#security-notes)
- [License](#license)

## Overview
SecureCloud encrypts files client‑side using AES‑256‑GCM, splits them into configurable blocks, and stores each block (and a JSON manifest) in an S3 bucket. A local key‑store holds the per‑file encryption keys, never uploaded to S3. The FastAPI backend exposes endpoints for health, upload, list, download and delete.

## Prerequisites
- Python 3.13 (or 3.12+)
- `pip` (>=24.0)
- (Optional) AWS credentials with permission to write to the bucket defined in `S3_BUCKET`
- Node is **not** required; the UI is plain HTML/JS.

## Setup
```powershell
# Clone the repo (if you haven't already)
git clone <repo‑url>
cd securecloud

# Create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

Create a `.env` file at `C:\cc-mini\.env` for this checkout. The backend loads it from the workspace root:
```
AWS_REGION=us-east-1
S3_BUCKET=your-globally-unique-bucket-name
# Optional overrides (defaults are shown)
# BLOCK_SIZE=1048576
# MAX_UPLOAD_SIZE=20971520
```
For AWS credentials, configure the AWS CLI or another standard AWS credential provider for the same Windows account that runs the backend. Without usable S3 access, the current storage adapter falls back to an in-memory mock; see the S3 guide for setup and verification.

## Using Amazon S3

Follow the [Amazon S3 setup guide](S3_SETUP.md) to create a private bucket, configure local AWS credentials and permissions, connect the backend, verify uploads, and understand Free Tier and key-backup considerations.

## Running the Application
```powershell
uvicorn backend.main:app --reload
```
The API will be available at `http://127.0.0.1:8000`.

Open the UI in a browser (you can serve it with any static server, e.g. `live-server` or just open the file directly):
```
start frontend\index.html
```
The UI talks to the API at the default address; adjust `API_BASE_URL` in `frontend/app.js` if you run the server elsewhere.

## API Reference
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Simple health check |
| POST | `/upload` | multipart `file` upload (max 20 MiB by default) |
| GET | `/files` | List all stored files (metadata from manifests) |
| GET | `/files/{file_id}` | Retrieve manifest for a specific file |
| GET | `/files/{file_id}/download` | Download the original file (decrypted on‑the‑fly) |
| DELETE | `/files/{file_id}` | Delete all blocks, manifest and local key |

## Frontend UI
The UI consists of three files under `frontend/`:
- `index.html` – layout and table
- `style.css` – basic responsive styling
- `app.js` – client‑side logic for upload, listing, download, delete
All files are already present in the repository.

## Testing
The project includes a `tests/` folder with `pytest` tests covering:
- Encryption helpers (`encryption.py`)
- Block splitting (`file_utils.py`)
- Mock storage behavior (`storage.py`)
- API integration using FastAPI’s `TestClient`
Run the suite with:
```powershell
pytest
```

## Deployment Scripts
Two PowerShell helper scripts are provided in `scripts/`:
- `deploy_portfolio.ps1` – syncs the `portfolio/` static site to an S3 bucket, creates/updates a CloudFront distribution, and invalidates the cache.
- `cleanup_aws.ps1` – safely removes the S3 bucket, CloudFront distribution and associated IAM policies. Both scripts prompt for confirmation before performing destructive actions.

## Portfolio Site
A minimal static site lives in `portfolio/` and showcases the architecture (Mermaid diagram), screenshots of the UI, and a short deployment guide. You can open `portfolio/index.html` locally or host it on any static web host (e.g., GitHub Pages, S3 static website hosting).

## Cost & Billing Guidance
- **Free Tier is account- and offer-dependent**: check the AWS Free Tier page and current S3 pricing for your account and region. Do not assume storage, requests, data transfer, or related services are free.
- **Budget alerts are notifications, not spending caps**: create a low AWS Budget alert and review actual usage and charges in Billing.
- See [Amazon S3 setup guide](S3_SETUP.md) for cost-control and safe cleanup steps. Do not run the portfolio cleanup script against your application bucket.

## Security Notes
- `.env` and the local key store (`securecloud_keys/`) are listed in `.gitignore` and never committed.
- Keys are stored **only on the backend**; they are never uploaded to S3.
- CORS is enabled for all origins in development. Restrict `allow_origins` in production.
- Use HTTPS in production (e.g., via CloudFront + ACM certificate).

## License
This sample project is released under the **MIT License**. Feel free to adapt, extend, or use it as a learning reference.
