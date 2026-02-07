from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(frozen=True)
class SheetsSource:
    """
    Connection metadata only. No secrets here.
    """
    spreadsheet_id: str
    worksheet_name: str


class SheetsClient:
    """
    Interface stub.

    Phase 3.5 intentionally does NOT choose a transport:
    - Google Sheets API
    - Apps Script Web App
    - CSV export

    Transport is Phase 3.6.
    """

    def __init__(self, source: SheetsSource):
        self.source = source

    def fetch_rows(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("Implement Sheets fetch in Phase 3.6+")
