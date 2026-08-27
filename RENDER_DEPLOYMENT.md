# Backend Deployment Guide for Render

This guide outlines how to initialize the FastAPI backend as a standalone GitHub repository, configure and deploy it as a Render Web Service, verify the endpoints, and compile the final Flutter release APK.

---

## 1. Standalone GitHub Setup

The backend repository must contain **only** the FastAPI backend code, not the entire Flutter workspace.

### Commands to Initialize and Push the Repository:
1. Open a terminal in the backend directory:
   ```bash
   cd c:\Users\keert\Downloads\Krishi222-fixed\krishivision_ai\backend
   ```
2. Initialize Git, stage all backend files, and commit:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of KrishiVision AI FastAPI backend"
   ```
3. Link and push to your private GitHub repository:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/krishivision-backend.git
   git branch -M main
   git push -u origin main
   ```

---

## 2. Render Web Service Configuration

1. Log in to [Render](https://dashboard.render.com/) and click **New > Web Service**.
2. Connect your newly pushed `krishivision-backend` GitHub repository.
3. Configure the Web Service:
   - **Name**: `krishivision-backend`
   - **Root Directory**: `.` (leave blank, since it is a standalone backend repo)
   - **Runtime**: `Docker`
   - **Plan**: `Free` (or standard Web Service)

---

## 3. Environment Variables (Server-Side Settings)

Configure these keys in the **Environment** tab on Render. **Never** include them in the client Flutter codebase:

| Key | Example / Description |
|---|---|
| `DATABASE_URL` | `postgresql://user:password@host:5432/dbname` *(Safest persistent option)* or `sqlite:///./krishivision.db` |
| `JWT_SECRET` | A secure cryptographically random key string for user JWT tokens |
| `AGROMONITORING_API_KEY` | `35c3682795c14edee7dd512a190128e5` |
| `DATA_GOV_API_KEY` | Your personal `data.gov.in` API key for crop statistics |

---

## 4. Build and Start Commands

Render automatically parses the `Dockerfile` to build and execute the container:

- **Build Command**: Render handles this automatically during Docker container compilation.
- **Start Command**:
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
  *(The Dockerfile is pre-configured to bind to `0.0.0.0` and utilize Render's dynamic `$PORT` environment variable)*

---

## 5. Seeding & Database Migration

Since Render's container disk is ephemeral, any SQLite file changes will be reset on restarts. We recommend using a persistent PostgreSQL database.
Once your web service is active, open the **Shell** tab on Render and run the following command once to import the master crop lists and state boundaries:
```bash
python load_sample_data.py
```

---

## 6. Deployed API Verification

Once deployed, test that the public URL returns HTTP `200` for these endpoints (replace `<public-domain>` with your active Render domain, e.g. `krishivision.onrender.com`):

- **Health Check**: `GET https://<public-domain>/health`
- **Docs (Swagger)**: `GET https://<public-domain>/docs`
- **State Crops**: `GET https://<public-domain>/apy/states/Karnataka/districts/Dharwad/crops`
- **Crop Satellite Details**: `GET https://<public-domain>/crops/1048/overview/growth/health`
- **PDF Report Generation**: `GET https://<public-domain>/crops/1048/report/pdf`

---

## 7. Flutter Client Configuration

1. Rebuild the release APK using the public Render URL (do not use trailing slashes):
   ```bash
   flutter clean
   flutter pub get
   flutter build apk --release --dart-define=BACKEND_URL=https://<your-public-domain>
   ```
2. Verify production priority is running by checking the startup console logs:
   `API BASE URL: https://<your-public-domain>`
