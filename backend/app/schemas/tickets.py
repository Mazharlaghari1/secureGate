from pydantic import BaseModel
from typing import List
from app.schemas.entities import TicketResponse

class TicketGenerateResponseData(BaseModel):
    generated: int

class TicketGenerateResponse(BaseModel):
    success: bool = True
    data: TicketGenerateResponseData

class TicketListResponse(BaseModel):
    success: bool = True
    data: List[TicketResponse]
    page: int
    page_size: int
    total: int

from datetime import datetime

class PublicTicketParticipant(BaseModel):
    name: str

class PublicTicketEvent(BaseModel):
    name: str
    venue: str
    date: str
    start_time: str
    end_time: str
    timezone: str

class PublicTicketDetail(BaseModel):
    ticket_code: str
    status: str
    participant: PublicTicketParticipant
    event: PublicTicketEvent
    expires_at: datetime
    qr_payload: str

class PublicTicketDetailResponse(BaseModel):
    success: bool = True
    data: PublicTicketDetail
