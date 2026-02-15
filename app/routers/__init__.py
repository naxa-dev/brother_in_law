"""Initialize router subpackage."""

from .dashboard import router as dashboard_router  # noqa: F401
from .admin import router as admin_router  # noqa: F401
from .crud_projects import router as projects_router  # noqa: F401
from .crud_events import router as events_router  # noqa: F401