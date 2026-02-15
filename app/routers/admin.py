"""
Admin router for sqlite backend.

Provides endpoints to view snapshots and upload new snapshot files.
"""

from fastapi import APIRouter, Depends, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from ..db import get_connection
from ..services.snapshot_importer import import_snapshot
from ..schemas import SnapshotBase, SnapshotReport

router = APIRouter()
from pathlib import Path

# Determine absolute template directory based on this file location.  The
# `routers` package sits under `app/routers`, while templates live in
# `app/templates`.  Therefore we ascend one directory above the current
# file's directory and join the `templates` folder.  Using an absolute
# path avoids issues when FastAPI reloader changes the working directory.
templates = Jinja2Templates(directory=str((Path(__file__).resolve().parent.parent) / "templates"))


def get_conn():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@router.get("/admin", response_class=HTMLResponse)
def admin_home(request: Request, conn = Depends(get_conn)):
    """Render the admin page with snapshots list and upload form."""
    snapshots = conn.execute("SELECT * FROM snapshots ORDER BY snapshot_date DESC").fetchall()
    return templates.TemplateResponse("admin.html", {"request": request, "snapshots": snapshots})


@router.post("/admin/upload", response_class=HTMLResponse)
async def upload_snapshot(request: Request, file: UploadFile = File(...), conn = Depends(get_conn)):
    """Handle snapshot upload."""
    report = import_snapshot(file)
    snapshots = conn.execute("SELECT * FROM snapshots ORDER BY snapshot_date DESC").fetchall()
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "snapshots": snapshots,
        "report": report
    })


@router.get("/api/snapshots", response_class=JSONResponse)
def list_snapshots(conn = Depends(get_conn)):
    """Return snapshots as JSON."""
    rows = conn.execute("SELECT * FROM snapshots ORDER BY snapshot_date DESC").fetchall()
    data = []
    for row in rows:
        data.append({
            "snapshot_id": row["snapshot_id"],
            "snapshot_date": row["snapshot_date"],
            "uploaded_at": row["uploaded_at"],
            "source_filename": row["source_filename"],
        })
    return data