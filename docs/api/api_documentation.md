# SADAR API Documentation

Base URL: `http://localhost:8000/api/v1`

## Core endpoints

- `GET /health` — API liveness.
- `POST /predict` — classify a spectrogram/features payload.
- `GET /predictions` — list stored prediction records.
- `GET /statistics` — label and alert summary.
- `GET /alerts` — list generated alerts.

## AI-agent endpoints

- `GET /agent/health`
- `POST /agent/ask`
- `POST /agent/analyze-threat`
- `POST /agent/report`
- `POST /agent/knowledge-base/rebuild`

Interactive docs are available at `/docs` when the API is running.
