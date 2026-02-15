"""
Metrics computation functions for sqlite backend.

Each function uses a provided sqlite3 connection to compute
aggregations needed for the dashboard. The connection must have
row_factory set to sqlite3.Row for dictionary-like row access.
"""

from typing import List, Tuple, Dict

import sqlite3


def compute_monthly_trend(conn: sqlite3.Connection, snapshot_id: int) -> Dict[str, List]:
    """Return month list and totals for proposals/approvals.

    Used for the top line chart ("추이") to give a cockpit-style overview.

    Returns:
        {
          "months": ["YYYY-MM", ...],
          "proposals": [int, ...],
          "approvals": [int, ...]
        }
    """
    months = get_snapshot_months(conn, snapshot_id)
    if not months:
        return {"months": [], "proposals": [], "approvals": []}

    c = conn.cursor()
    proposals: List[int] = []
    approvals: List[int] = []
    for m in months:
        c.execute(
            """
            SELECT
              SUM(CASE WHEN is_new_proposal = 1 THEN 1 ELSE 0 END) AS p_cnt,
              SUM(CASE WHEN is_approved = 1 THEN 1 ELSE 0 END) AS a_cnt
            FROM project_monthly_events
            WHERE snapshot_id = ? AND month_key = ?
            """,
            (snapshot_id, m),
        )
        row = c.fetchone()
        proposals.append(int(row[0] or 0))
        approvals.append(int(row[1] or 0))

    return {"months": months, "proposals": proposals, "approvals": approvals}


def compute_status_distribution(conn: sqlite3.Connection, snapshot_id: int) -> List[Tuple[str, int]]:
    """Count projects by current_status for a snapshot."""
    c = conn.cursor()
    c.execute(
        """
        SELECT current_status, COUNT(*) AS cnt
        FROM projects
        WHERE snapshot_id = ?
        GROUP BY current_status
        """,
        (snapshot_id,),
    )
    rows = [(row[0] or '(blank)', int(row[1] or 0)) for row in c.fetchall()]
    rows.sort(key=lambda x: -x[1])
    return rows


def compute_active_by_strategy(conn: sqlite3.Connection, snapshot_id: int) -> List[Tuple[str, int]]:
    """Count active projects by strategy category (snapshot scope)."""
    c = conn.cursor()
    c.execute("SELECT strategy_id, name FROM strategy_categories")
    strat_map = {row['strategy_id']: row['name'] for row in c.fetchall()}
    strat_map[None] = '(미할당)'

    c.execute(
        """
        SELECT strategy_id AS sid, COUNT(*) AS cnt
        FROM projects
        WHERE snapshot_id = ? AND current_status = '승인(진행중)'
        GROUP BY strategy_id
        """,
        (snapshot_id,),
    )
    result = []
    for row in c.fetchall():
        result.append((strat_map.get(row['sid'], '(미할당)'), int(row['cnt'] or 0)))

    # Include zero counts for known categories (keeps chart stable)
    existing = {name for name, _ in result}
    for _, name in strat_map.items():
        if name not in existing:
            result.append((name, 0))

    result.sort(key=lambda x: (-x[1], x[0] or ''))
    return result


def get_snapshot_months(conn: sqlite3.Connection, snapshot_id: int) -> List[str]:
    c = conn.cursor()
    c.execute(
        "SELECT DISTINCT month_key FROM project_monthly_events WHERE snapshot_id = ?",
        (snapshot_id,)
    )
    months = [row[0] for row in c.fetchall()]
    months.sort()
    return months


def compute_kpis(conn: sqlite3.Connection, snapshot_id: int, month: str) -> Dict:
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM projects WHERE snapshot_id = ?", (snapshot_id,))
    total_projects = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(*) FROM projects WHERE snapshot_id = ? AND current_status = '승인(진행중)'",
        (snapshot_id,)
    )
    total_active = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(*) FROM project_monthly_events WHERE snapshot_id = ? AND month_key = ? AND is_new_proposal = 1",
        (snapshot_id, month)
    )
    month_proposals = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(*) FROM project_monthly_events WHERE snapshot_id = ? AND month_key = ? AND is_approved = 1",
        (snapshot_id, month)
    )
    month_approvals = c.fetchone()[0]
    # participation rate
    c.execute(
        "SELECT COUNT(DISTINCT champion_id) FROM project_monthly_events WHERE snapshot_id = ? AND month_key = ? AND (is_new_proposal = 1 OR is_approved = 1)",
        (snapshot_id, month)
    )
    active_champions = c.fetchone()[0]
    c.execute(
        "SELECT COUNT(DISTINCT champion_id) FROM projects WHERE snapshot_id = ?",
        (snapshot_id,)
    )
    total_champions = c.fetchone()[0]
    participation_rate = (active_champions / total_champions) if total_champions else 0.0
    approval_conversion_rate = (month_approvals / month_proposals) if month_proposals else 0.0
    return {
        'total_projects': total_projects,
        'total_active_projects': total_active,
        'month_proposals': month_proposals,
        'month_approvals': month_approvals,
        'champion_participation_rate': round(participation_rate, 2),
        'approval_conversion_rate': round(approval_conversion_rate, 2),
    }


def compute_ranking(conn: sqlite3.Connection, snapshot_id: int, month: str) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]], List[Tuple[str, int]]]:
    c = conn.cursor()
    # Get champion names mapping
    c.execute("SELECT champion_id, name FROM champions")
    champ_map = {row['champion_id']: row['name'] for row in c.fetchall()}
    champ_map[None] = '(미할당)'
    # Proposals
    c.execute(
        "SELECT champion_id, COUNT(*) AS cnt FROM project_monthly_events WHERE snapshot_id = ? AND month_key = ? AND is_new_proposal = 1 GROUP BY champion_id",
        (snapshot_id, month)
    )
    proposal_counts = {row['champion_id']: row['cnt'] for row in c.fetchall()}
    # Approvals
    c.execute(
        "SELECT champion_id, COUNT(*) AS cnt FROM project_monthly_events WHERE snapshot_id = ? AND month_key = ? AND is_approved = 1 GROUP BY champion_id",
        (snapshot_id, month)
    )
    approval_counts = {row['champion_id']: row['cnt'] for row in c.fetchall()}
    # Active
    c.execute(
        "SELECT champion_id, COUNT(*) AS cnt FROM projects WHERE snapshot_id = ? AND current_status = '승인(진행중)' GROUP BY champion_id",
        (snapshot_id,)
    )
    active_counts = {row['champion_id']: row['cnt'] for row in c.fetchall()}
    # Convert to list of tuples
    proposal_ranking = [(champ_map.get(cid), count) for cid, count in proposal_counts.items()]
    approval_ranking = [(champ_map.get(cid), count) for cid, count in approval_counts.items()]
    active_ranking = [(champ_map.get(cid), count) for cid, count in active_counts.items()]
    proposal_ranking.sort(key=lambda x: (-x[1], x[0] or ''))
    approval_ranking.sort(key=lambda x: (-x[1], x[0] or ''))
    active_ranking.sort(key=lambda x: (-x[1], x[0] or ''))
    return proposal_ranking, approval_ranking, active_ranking


def compute_distribution(conn: sqlite3.Connection, snapshot_id: int, month: str) -> List[Tuple[str, int, int, int]]:
    c = conn.cursor()
    # Get strategy name mapping
    c.execute("SELECT strategy_id, name FROM strategy_categories")
    strat_map = {row['strategy_id']: row['name'] for row in c.fetchall()}
    strat_map[None] = '(미할당)'
    # Initialise distribution dict
    distribution: Dict[int, Dict[str, int]] = {}
    for sid in strat_map.keys():
        distribution[sid] = {'proposals': 0, 'approvals': 0, 'active': 0}
    # Proposals by strategy
    c.execute(
        """
        SELECT projects.strategy_id AS sid, COUNT(*) AS cnt
        FROM project_monthly_events AS e
        JOIN projects ON e.snapshot_id = projects.snapshot_id AND e.project_id = projects.project_id
        WHERE e.snapshot_id = ? AND e.month_key = ? AND e.is_new_proposal = 1
        GROUP BY projects.strategy_id
        """,
        (snapshot_id, month)
    )
    for row in c.fetchall():
        distribution[row['sid']]['proposals'] = row['cnt']
    # Approvals by strategy
    c.execute(
        """
        SELECT projects.strategy_id AS sid, COUNT(*) AS cnt
        FROM project_monthly_events AS e
        JOIN projects ON e.snapshot_id = projects.snapshot_id AND e.project_id = projects.project_id
        WHERE e.snapshot_id = ? AND e.month_key = ? AND e.is_approved = 1
        GROUP BY projects.strategy_id
        """,
        (snapshot_id, month)
    )
    for row in c.fetchall():
        distribution[row['sid']]['approvals'] = row['cnt']
    # Active by strategy
    c.execute(
        "SELECT strategy_id AS sid, COUNT(*) AS cnt FROM projects WHERE snapshot_id = ? AND current_status = '승인(진행중)' GROUP BY strategy_id",
        (snapshot_id,)
    )
    for row in c.fetchall():
        distribution[row['sid']]['active'] = row['cnt']
    # Convert to list
    result = []
    for sid, vals in distribution.items():
        result.append((strat_map[sid], vals['proposals'], vals['approvals'], vals['active']))
    result.sort(key=lambda x: x[0])
    return result


def compute_heatmap(conn: sqlite3.Connection, snapshot_id: int) -> Dict[str, Dict[str, Dict[str, int]]]:
    c = conn.cursor()
    # Champion names mapping
    c.execute("SELECT champion_id, name FROM champions")
    champ_map = {row['champion_id']: row['name'] for row in c.fetchall()}
    champ_map[None] = '(미할당)'
    # Months
    months = get_snapshot_months(conn, snapshot_id)
    heatmap: Dict[str, Dict[str, Dict[str, int]]] = {}
    # initialize
    for cid, cname in champ_map.items():
        heatmap[cname] = {m: {'proposals': 0, 'approvals': 0} for m in months}
    # proposals per champion per month
    c.execute(
        """
        SELECT champion_id, month_key, COUNT(*) AS cnt
        FROM project_monthly_events
        WHERE snapshot_id = ? AND is_new_proposal = 1
        GROUP BY champion_id, month_key
        """,
        (snapshot_id,)
    )
    for row in c.fetchall():
        cname = champ_map.get(row['champion_id'])
        if cname:
            heatmap[cname][row['month_key']]['proposals'] = row['cnt']
    # approvals per champion per month
    c.execute(
        """
        SELECT champion_id, month_key, COUNT(*) AS cnt
        FROM project_monthly_events
        WHERE snapshot_id = ? AND is_approved = 1
        GROUP BY champion_id, month_key
        """,
        (snapshot_id,)
    )
    for row in c.fetchall():
        cname = champ_map.get(row['champion_id'])
        if cname:
            heatmap[cname][row['month_key']]['approvals'] = row['cnt']
    return heatmap