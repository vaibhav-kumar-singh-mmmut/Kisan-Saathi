"""
Jurisdiction scope service.

Core of the "one route, server-side filter" design from AI_AGENT_BUILD_PROMPT.md Phase 2.

get_village_ids_in_scope(db, jurisdiction_id, jurisdiction_type) → list[str]
  - District-level → all village IDs in the district
  - Tehsil-level   → all village IDs in the tehsil
  - Block-level    → all village IDs in the block
  - Village-level  → only that village's ID

Uses a recursive SQL CTE to walk the jurisdictions self-referencing tree.
This keeps the logic in one place — no per-role branching in the endpoint.
"""

from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

# Roles that map to district scope regardless of their jurisdiction_id
_DISTRICT_SCOPE_ROLES = {
    "DM",
    "District Magistrate",
    "Adl. Commissioner",
    "Adl. DM (F/R)",
    "Adl. DM (E)",
    "Adl. DM (City)",
    "Chief Revenue Officer",
    "CDO",
    "Chief Development Officer",
    "DDO",
    "District Development Officer",
    "KVK Expert",  # assigned to district queue
}

# Roles that map to block scope
_BLOCK_SCOPE_ROLES = {
    "BDO",
    "Block Development Officer",
    "Agriculture Officer",
    "Agriculture/Horticulture Officer",
    "Horticulture Officer",
    "DC (MGNREGA)",
    "DC (NRLM)",
    "Project Director (DRDA)",
    "PD (DRDA)",
}

# Roles that map to tehsil scope
_TEHSIL_SCOPE_ROLES = {
    "Tehsildar",
    "Naib Tehsildar",
    "SDM",
    "Sub Divisional Magistrate",
    "Kanungo",
}

# Roles that map to their own village/block (stored jurisdiction_id)
_VILLAGE_SCOPE_ROLES = {
    "Farmer",
    "Pradhan",
    "Lekhpal/Patwari",
    "Lekhpal",
    "Patwari",
}

# Service roles — scoped to their assigned jurisdiction_id (could be block or village)
_SERVICE_SCOPE_ROLES = {
    "RPTO Drone Pilot",
    "Drone Pilot",
    "Drone Assistant",
    "CHC Manager",
    "FPO Representative",
    "FPO Rep",
}


def resolve_scope_type(role: str, jurisdiction_type: str) -> str:
    """
    Given the role from the JWT, return the effective scope type.
    Falls back to the jurisdiction_type stored in the officials table.
    """
    if role in _DISTRICT_SCOPE_ROLES:
        return "district"
    if role in _BLOCK_SCOPE_ROLES:
        return "block"
    if role in _TEHSIL_SCOPE_ROLES:
        return "tehsil"
    # Village-level and service roles: use whatever is stored
    return jurisdiction_type


def get_village_ids_in_scope(
    db: Session,
    jurisdiction_id: str,
    role: str,
    stored_jurisdiction_type: str,
) -> list[str]:
    """
    Return the list of village jurisdiction IDs visible to this caller.

    Uses a recursive CTE:
      1. Start at jurisdiction_id (the caller's node)
      2. Walk down to all descendants
      3. Filter to jurisdiction_type = 'village'
    """
    if not jurisdiction_id:
        return []

    scope_type = resolve_scope_type(role, stored_jurisdiction_type)

    # For village-scoped users, return just their own village
    if scope_type == "village":
        return [jurisdiction_id]

    # For all broader scopes: find the right ancestor then collect all descendant villages
    # Step 1: find the correct ancestor node at the target scope level
    #   (the junction already IS at that level if scope == stored_jurisdiction_type)
    ancestor_id = _find_ancestor_at_level(db, jurisdiction_id, scope_type)
    if not ancestor_id:
        # Fallback: treat own jurisdiction as the root
        ancestor_id = jurisdiction_id

    # Step 2: recursive CTE to collect all village descendants
    cte_sql = text("""
        WITH RECURSIVE descendants AS (
            SELECT id, jurisdiction_type FROM jurisdictions WHERE id = :root_id
            UNION ALL
            SELECT j.id, j.jurisdiction_type
            FROM jurisdictions j
            INNER JOIN descendants d ON j.parent_id = d.id
        )
        SELECT id FROM descendants WHERE jurisdiction_type = 'village'
    """)

    rows = db.execute(cte_sql, {"root_id": ancestor_id}).fetchall()
    return [row[0] for row in rows]


def _find_ancestor_at_level(
    db: Session, start_id: str, target_type: str
) -> Optional[str]:
    """
    Walk up the jurisdictions tree from start_id until we reach a node
    with jurisdiction_type == target_type. Returns that node's id, or None.
    """
    walk_sql = text("""
        WITH RECURSIVE ancestors AS (
            SELECT id, jurisdiction_type, parent_id FROM jurisdictions WHERE id = :start_id
            UNION ALL
            SELECT j.id, j.jurisdiction_type, j.parent_id
            FROM jurisdictions j
            INNER JOIN ancestors a ON j.id = a.parent_id
        )
        SELECT id FROM ancestors WHERE jurisdiction_type = :target_type LIMIT 1
    """)
    row = db.execute(
        walk_sql, {"start_id": start_id, "target_type": target_type}
    ).fetchone()
    return row[0] if row else None
