from pydantic import BaseModel
from typing import List
from datetime import datetime

class VerifyTicketRequest(BaseModel):
    token: str
    event_id: str

class VerifyTicketResponseParticipant(BaseModel):
    name: str

class VerifyTicketResponseEvent(BaseModel):
    name: str

class VerifyTicketResponseScanner(BaseModel):
    name: str

class VerifyTicketResponseData(BaseModel):
    status: str = "valid"
    participant: VerifyTicketResponseParticipant
    ticket_code: str
    event: VerifyTicketResponseEvent
    scanned_at: datetime
    scanned_by: VerifyTicketResponseScanner

class VerifyTicketResponse(BaseModel):
    success: bool = True
    data: VerifyTicketResponseData

class StaffScanHistoryItem(BaseModel):
    ticket_code: str
    participant_name: str
    event_name: str
    scanned_at: datetime
    status: str = "valid"

class StaffScanHistoryResponse(BaseModel):
    success: bool = True
    data: List[StaffScanHistoryItem]
    page: int
    page_size: int
    total: int
