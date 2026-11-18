# FRAME — Creator Studio (Vercel & Streamlit Cloud Package)

This repository is cleanly structured for cloud deployment with **no local startup scripts**.

## 1. Deploy to Vercel
- **Files used:** `index.html` and `vercel.json`
- **How to deploy:**
  1. Go to [vercel.com/new](https://vercel.com/new).
  2. Either drag-and-drop this extracted folder directly onto Vercel, or import your GitHub repository.
  3. Click **Deploy** (deploys in ~3 seconds via `@vercel/static`).

## 2. Deploy to Streamlit Community Cloud
- **Files used:** `streamlit_app.py` and `requirements.txt`
- **How to deploy:**
  1. Push this folder to a GitHub repository.
  2. Go to [share.streamlit.io](https://share.streamlit.io) and click **Create app**.
  3. Select your repository, set **Main file path** to `streamlit_app.py`, and click **Deploy**.
