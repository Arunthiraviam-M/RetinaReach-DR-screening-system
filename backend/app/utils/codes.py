from __future__ import annotations

import re
from datetime import datetime

from app.models.patient import Patient


async def generate_patient_code() -> str:
    """
    Generates human-friendly, sequential patient IDs like RS-2026-000123.
    Sequence resets each calendar year, matching how most district health
    programs like their register numbers to look.
    """
    year = datetime.now().year
    prefix = f"RS-{year}-"
    pattern = re.compile(f"^{re.escape(prefix)}")
    count_this_year = await Patient.find({"patient_code": {"$regex": pattern}}).count()
    next_number = count_this_year + 1
    return f"{prefix}{next_number:06d}"
