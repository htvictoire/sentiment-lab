"""Application FastAPI du tableau de bord de sentiment."""

from datetime import datetime, timezone

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

import settings
import storage
from analytics import serialize_message, summary_payload
from local_model import is_model_ready
from uploads import extract_chat_text, import_records, parse_chat_export


app = FastAPI(title="WhatsApp Sentiment API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.CORS_ALLOWED_ORIGINS),
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)
storage.init_db()


@app.get("/api/health/")
def health():
    return {
        "status": "ok",
        "service": "fastapi-backend",
        "model": settings.LOCAL_MODEL_NAME,
        "local_model_ready": is_model_ready(),
    }


@app.get("/api/messages/")
def messages(
    limit: int = Query(default=50, ge=1, le=200),
    label: str = "",
    q: str = "",
):
    rows = storage.fetch_messages(limit=limit, label=label.strip(), query=q.strip())
    return {"messages": [serialize_message(row) for row in rows]}


@app.delete("/api/messages/", status_code=200)
def delete_all_messages():
    storage.clear_messages()
    return {"status": "ok"}


@app.get("/api/dashboard/summary/")
def summary(days: int = Query(default=7, ge=1, le=90), since: str = "", until: str = ""):
    if since and until:
        try:
            start = datetime.fromisoformat(since).replace(tzinfo=timezone.utc)
            end = datetime.fromisoformat(until).replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Dates 'since'/'until' invalides (format AAAA-MM-JJ).") from exc
        if start > end:
            raise HTTPException(status_code=400, detail="'since' doit être antérieure à 'until'.")
        return summary_payload(start=start, end=end)
    return summary_payload(days)


@app.post("/api/messages/import/", status_code=201)
async def import_chat(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Attach a WhatsApp chat export as 'file'.")
    try:
        data = await file.read()
        content = extract_chat_text(data, file.filename)
        records = parse_chat_export(content)
        if not records:
            raise ValueError(f"No WhatsApp messages were found in {file.filename}.")
        result = import_records(
            records,
        )
        return {"result": result}
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
