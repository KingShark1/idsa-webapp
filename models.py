from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List, Optional

Base = declarative_base()

class Swimmer(Base):
    __tablename__ = "swimmers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    dob = Column(String)
    age_group = Column(Integer)
    gender = Column(String)
    club = Column(String)
    sfi_id = Column(String, default=None)
    events = relationship("SwimmerEvent", back_populates="swimmer")  # Define the relationship

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age_group = Column(Integer)
    gender = Column(String)
    swimmers = relationship("SwimmerEvent", back_populates="event")

class SwimmerEvent(Base):
    __tablename__ = "swimmer_events"
    id = Column(Integer, primary_key=True, index=True)
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    medal = Column(Integer)
    time = Column(String)
    lane_id = Column(Integer)
    heat_id = Column(Integer)
    swimmer = relationship("Swimmer", back_populates="events")
    event = relationship("Event", back_populates="swimmers")

# Pydantic models for responses
class EventModel(BaseModel):
    id: int
    name: str
    age_group: int
    gender: str
    participants: List['SwimmerEventModel'] = []

    class Config:
        orm_mode = True

class SwimmerModel(BaseModel):
    id: int
    name: str
    dob: Optional[str]
    age_group: int
    gender: str
    club: Optional[str]
    sfi_id: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True

class SwimmerUpdateModel(BaseModel):
    id: int
    name: str
    dob: Optional[str]
    gender: str
    club: Optional[str]
    sfi_id: Optional[str]

    class Config:
        orm_mode = True
        from_attributes = True

class SwimmerEventModel(BaseModel):
    id: int
    swimmer_id: int
    event_id: int
    heat_id: int
    lane_id: int
    medal: Optional[str]
    time: Optional[str]
    swimmer: SwimmerModel

    class Config:
        orm_mode = True

class UpdateTimeRequest(BaseModel):
    swimmer_event_id: int
    time: str

class UpdateLaneOrder(BaseModel):
    heat_id: int
    lane_id: int
    swimmer_event_id: str
# Resolve forward reference
EventModel.update_forward_refs()
