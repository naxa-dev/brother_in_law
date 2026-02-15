# AX Dashboard

This project is a self‑contained FastAPI application for managing and visualising AX projects. It allows administrators to upload Excel snapshots, correct data through CRUD interfaces, and provides an interactive dashboard for stakeholders to monitor proposals, approvals and ongoing projects.

## Features

* **Excel Upload**: Upload snapshot files named `YYYY-MM-DD.xlsx` with an `AX_Master` sheet and monthly sheets (e.g. `2026-02`).
* **Snapshot Storage**: Snapshots are persisted in an SQLite database (`db/ax.db`). Duplicate dates are rejected.
* **Dashboard**: Shows active projects by champion, monthly rankings for proposals and approvals, KPI cards, strategy distributions, and a heatmap of champion activity.
* **CRUD Interfaces**: Manage projects and monthly events via simple forms. All changes are logged in audit logs.
* **Charts and Heatmap**: Utilises Chart.js for bar charts and CSS for a basic heatmap.

## Running Locally

Ensure Python 3.10+ is installed. Then install dependencies and start the server:

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ax_dashboard
uvicorn app.main:app --reload
```

Access the dashboard at `http://localhost:8000`. Use the admin interface at `http://localhost:8000/admin` to upload snapshots and manage data.

## Directory Structure

```
ax_dashboard/
├── app/
│   ├── main.py             # FastAPI entry point
│   ├── database.py         # SQLAlchemy engine and session
│   ├── models.py           # ORM models
│   ├── schemas.py          # Pydantic schemas
│   ├── services/           # Business logic (import, metrics, audit)
│   ├── routers/            # API and web routes
│   ├── templates/          # Jinja2 templates
│   └── static/             # CSS and JS assets
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## Notes

* For CORS safety, the API and frontend are served from the same FastAPI application.
* The default strategy categories are created when first encountered in uploads.
* The heatmap colour intensity is proportional to the sum of proposals and approvals per cell.
