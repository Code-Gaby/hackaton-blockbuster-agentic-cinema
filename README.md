# 🎬 Agentic Cinema Studio — Studio Co-Director AI

> **Google Cloud Agentic Cinema Hackathon — Parallel Track**  
> Autonomous multi-agent film director & studio intelligence platform powered by **Google Gemini**, **Google Cloud Agent Builder**, and **Parallel Search API**.

---

## 🌟 Overview

**Agentic Cinema Studio** transforms professional film pre-production from a fragmented, months-long endeavor into an interactive, real-time studio workspace. Acting as an autonomous **Studio Co-Director AI**, the platform orchestrates a collaborative network of specialized creative and logistical AI agents to write screenplays, track narrative continuity, estimate budgets, optimize shooting schedules, and scout authentic real-world filming locations.

---

## 🏗️ System Architecture

Agentic Cinema Studio uses a decoupled, multi-agent architecture built on **Google Cloud** infrastructure:

```text
                               +-------------------------------------------------+
                               |           DIRECTOR (User / Studio Lead)         |
                               +-------------------------------------------------+
                                                        |
                                          (Prompts / UI Actions / Approvals)
                                                        v
                               +-------------------------------------------------+
                               |             STUDIO CO-DIRECTOR AI               |
                               |    (DirectorAgent Orchestrator - Gemini 2.5)    |
                               +-------------------------------------------------+
                                 /            |              |                                                 /             |              |                                                 v              v              v                   v
        +-------------------------+  +------------------+  +------------------+  +------------------+
        |       StoryEngine       |  |   SceneEngine    |  | ContinuityEngine |  |  ProductionIntel |
        | (Beats, Arcs, Dialogue) |  | (Locations, Sets)|  | (Knowledge Leaks)|  | (Budget & Sched) |
        +-------------------------+  +------------------+  +------------------+  +------------------+
                     |                        |                      |                    |
                     +------------------------+----------------------+--------------------+
                                                        |
                                                        v
                               +-------------------------------------------------+
                               |             PARALLEL SEARCH API (SDK)           |
                               |   Live Real-World Location & Historical Ground  |
                               +-------------------------------------------------+
                                                        |
                                                        v
                               +-------------------------------------------------+
                               |        ZERO MUTATION GATE (Safety & Rollback)   |
                               |          SQLite Relational State & Snapshots    |
                               +-------------------------------------------------+
```

---

## 🚀 Key Features

### 1. 🌐 "Scout with Parallel" (Core Runtime Workflow)
* **Live Web Intelligence:** Directly integrated on every Scene card and detail modal.
* **Scene-Aware Objectives:** Formulates targeted search objectives based on slugline, location, environment, time-of-day, and cinematic tone.
* **Autonomous Parallel Retrieval:** Calls the official `parallel-web` SDK at runtime to discover real-world locations matching visual and architectural requirements.
* **Gemini Co-Director Ranking:** Gemini evaluates retrieved web sources, ranking the top 3 candidates with **Narrative Fit**, **Production Logistics**, and **Proposed Diffs**.
* **Zero Mutation Gate:** Real-world data is presented as a proposal; no changes are committed to the screenplay or database until the Director explicitly clicks **"Use This Location"**.

### 2. 🤖 Google Cloud Agent Builder & Gemini Ecosystem
* **Google Gemini (google-genai):** Powered by `gemini-2.5-flash` for high-speed narrative synthesis and `gemini-3.5-flash` for multi-modal reasoning and screenplay generation.
* **Google Cloud Agent Builder Bridge:** Complete OpenAPI 3.0 tool manifest (`/api/agent_builder/spec`) and agent manifest (`/api/agent_builder/manifest`) ready for 1-click import into Google Cloud Vertex AI Agent Builder.
* **Enterprise Grounding:** Bridge architecture connects to Vertex AI Search datastores when Google Cloud project credentials are provided.

### 3. 🛡️ Zero Mutation Gate & Instant Rollback
* **Safety By Design:** Film projects are high-value creative assets. Agentic Cinema Studio guarantees that autonomous agents *never* destructively overwrite scenes or canon without Director approval.
* **Immutable Snapshot History:** Every applied location or script modification automatically creates a snapshot in `scene_versions` and records an event in `project_history`, enabling instant single-click rollbacks.

### 4. 📜 Hollywood Standard Formatting & Exports
* **Industry Screenplay Standard:** Formats sluglines (`INT./EXT.`), scene action blocks, character cues, and parentheticals.
* **Multi-Format Downloads:** Export clean Hollywood-formatted PDF documents and `.docx` Word files.

### 5. 🌍 Complete Multilingual UI (6 Languages)
* Full parity across **English** (Default), **Spanish**, **German**, **French**, **Italian**, and **Portuguese** for navigation, scene breakdown, continuity alerts, character dossiers, and Parallel Search scouting reports.

---

## 🛠️ Tech Stack

* **Backend:** Python 3.11, Flask, Gunicorn
* **AI & Orchestration:** `google-genai` (Gemini 2.5 / 3.5), Google Cloud Agent Builder Bridge
* **Partner Technology:** `parallel-web` (Parallel Search API)
* **Database & Persistence:** SQLite 3 (WAL mode, relational integrity, version snapshots)
* **Frontend:** Modern studio UI with Glassmorphism, responsive grid layout, vanilla JavaScript (Zero-dependency frontend for ultra-fast load times)
* **Containerization:** Docker, optimized for **Google Cloud Run**

---

## ⚡ Quickstart

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/agentic-cinema.git
cd agentic-cinema
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux / macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and add your API keys:
```ini
# Google Gemini API Key (Google AI Studio / Vertex AI)
GEMINI_API_KEY=AIzaSy...

# Parallel Search API Key (platform.parallel.ai)
PARALLEL_API_KEY=par_...

# Optional: Google Cloud Agent Builder Grounding
GOOGLE_CLOUD_PROJECT=your_gcp_project_id
GOOGLE_CLOUD_LOCATION=us-central1
AGENT_BUILDER_DATASTORE_ID=your_datastore_id
```

### 5. Launch the Studio
```bash
python app.py
```
Open your browser at **`http://127.0.0.1:5000`**.

---

## ☁️ Deploy to Google Cloud Run

Deploy directly from source using the Google Cloud CLI:

```bash
gcloud run deploy agentic-cinema \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY="your_key",PARALLEL_API_KEY="your_key"
```

Or build and push the Docker container:
```bash
docker build -t gcr.io/$PROJECT_ID/agentic-cinema:latest .
docker push gcr.io/$PROJECT_ID/agentic-cinema:latest
gcloud run deploy agentic-cinema --image gcr.io/$PROJECT_ID/agentic-cinema:latest --port 5000
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/scenes/<scene_id>/scout_parallel` | Autonomous real-world location scouting via Parallel Search API & Gemini |
| `POST` | `/api/scenes/<scene_id>/apply_scouted_location` | Zero Mutation Gate approval & SQLite scene update |
| `POST` | `/api/chat` | Conversational Studio Co-Director orchestrator |
| `GET` | `/api/agent_builder/spec` | OpenAPI 3.0 specification for Google Cloud Agent Builder |
| `GET` | `/api/agent_builder/manifest` | Google Cloud Agent Builder Application Manifest |
| `GET` | `/api/projects/<id>/export/docx` | Hollywood-standard DOCX screenplay export |

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
