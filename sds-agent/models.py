from pydantic import BaseModel
from typing import List, Optional

class SiteMemory(BaseModel):
    domain: str
    entry_path: Optional[str] = None
    pagination_type: Optional[str] = None
    download_pattern: Optional[str] = None
    last_success: bool = False

class AgentAction(BaseModel):
    action: str  # click | paginate | extract | stop
    target: Optional[str] = None
