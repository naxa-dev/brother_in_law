"""
Pydantic schema definitions for request and response models.

These schemas define the shape of data returned by API endpoints.
Using schemas ensures that responses are well structured and validated.
"""

from datetime import date, datetime
from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class SnapshotBase(BaseModel):
    snapshot_id: int
    snapshot_date: date
    uploaded_at: datetime
    source_filename: str

    pass


class SnapshotReport(BaseModel):
    """Report returned after importing a snapshot.

    Contains counts of processed projects and events along with any
    warnings or errors encountered during import.
    """

    success: bool
    message: str
    processed_projects: int
    processed_events: int
    warnings: List[str]
    errors: List[str]


class KPIResponse(BaseModel):
    """Key performance indicators for dashboard."""

    total_projects: int
    total_active_projects: int
    month_proposals: int
    month_approvals: int
    champion_participation_rate: float
    approval_conversion_rate: float


class RankingEntry(BaseModel):
    champion: str
    count: int


class DistributionEntry(BaseModel):
    category: str
    proposals: int
    approvals: int
    active: int


class HeatmapCell(BaseModel):
    champion: str
    month: str
    proposals: int
    approvals: int


class DashboardData(BaseModel):
    kpis: KPIResponse
    proposal_ranking: List[RankingEntry]
    approval_ranking: List[RankingEntry]
    active_ranking: List[RankingEntry]
    distribution: List[DistributionEntry]
    heatmap: List[HeatmapCell]

    pass