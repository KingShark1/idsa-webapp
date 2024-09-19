from sqlalchemy import Column, Integer, String, ForeignKey, Date, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List, Optional

Base = declarative_base()

# Association table to link swimmers and relay events
relay_swimmer_association = Table(
    'relay_swimmer_association',
    Base.metadata,
    Column('relay_event_id', Integer, ForeignKey('relay_events.id')),
    Column('swimmer_id', Integer, ForeignKey('swimmers.id'))
)

class Swimmer(Base):
    __tablename__ = "swimmers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    dob = Column(String)
    age_group = Column(Integer)
    gender = Column(String)
    club = relationship("Club", back_populates="swimmers")
    club_id = Column(Integer, ForeignKey('clubs.id'))
    sfi_id = Column(String, default=None)
    events = relationship("SwimmerEvent", back_populates="swimmer")  # Define the relationship
    relay_events = relationship("RelayEvent", secondary=relay_swimmer_association, back_populates="swimmers")
    final_events = relationship("FinalEvent", back_populates="swimmer")


class Club(Base):
    __tablename__ = "clubs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    total_points = Column(Integer)
    swimmers = relationship("Swimmer", back_populates="club")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age_group = Column(Integer)
    gender = Column(String)
    time_trial = Column(Boolean)
    swimmers = relationship("SwimmerEvent", back_populates="event")
    final_events = relationship("FinalEvent", back_populates="event")
    relay_events = relationship("RelayEvent", back_populates="event")


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

class RelayEvent(Base):
    __tablename__ = "relay_events"

    id = Column(Integer, primary_key=True, index=True)
    club_id = Column(Integer, ForeignKey('clubs.id'))
    event_id = Column(Integer, ForeignKey('events.id'))
    medal = Column(Integer)
    lane_id = Column(Integer)
    heat_id = Column(Integer)
    time = Column(String)
    club = relationship("Club", back_populates="relay_events")
    swimmers = relationship("Swimmer", secondary=relay_swimmer_association, back_populates="relay_events")
    event = relationship("Event", back_populates="relay_events")

class FinalEvent(Base):
    __tablename__ = "final_events"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    swimmer_id = Column(Integer, ForeignKey("swimmers.id"))
    time = Column(String)
    medal = Column(Integer)
    event = relationship("Event", back_populates="final_events")
    swimmer = relationship("Swimmer", back_populates="final_events")

Club.relay_events = relationship("RelayEvent", back_populates="club")
# Pydantic models for responses
class EventModel(BaseModel):
    id: int
    name: str
    age_group: int
    gender: str
    participants: List['SwimmerEventModel'] = []

    class Config:
        from_attributes = True

class ClubModel(BaseModel):
    name: str
    total_points: int = 0  # Optional field with a default value

class SwimmerModel(BaseModel):
    id: int
    name: str
    dob: Optional[str]
    age_group: int
    gender: str
    club: Optional[ClubModel]
    sfi_id: Optional[str]

    class Config:
        from_attributes = True

class SwimmerEventForCompetitionModel(BaseModel):
    id: int
    name: str
    dob: str
    age_group: int
    gender: str
    club: Optional[ClubModel]  # or you can have it as a dictionary if you need more info, e.g., club: dict
    events: List[str]  # A list of events that the swimmer is participating in
    relay_events: List[str]

    class Config:
        orm_mode = True

class SwimmerUpdateModel(BaseModel):
    id: int
    name: str
    dob: Optional[str]
    gender: str
    club: Optional[ClubModel]
    sfi_id: Optional[str]

    class Config:
        from_attributes = True
        from_attributes = True

class SwimmerEventModel(BaseModel):
    id: int
    swimmer_id: int
    event_id: int
    heat_id: int
    lane_id: int
    medal: Optional[int]
    time: Optional[str]
    swimmer: SwimmerModel

    class Config:
        from_attributes = True

class UpdateSwimmerTimeRequest(BaseModel):
    swimmer_event_id: int
    time: str

class UpdateRelayTimeRequest(BaseModel):
    relay_event_id: int
    time: str

class UpdateLaneOrder(BaseModel):
    heat_id: int
    lane_id: int
    swimmer_event_id: str

class RelayEventPydantic(BaseModel):
    id: int
    club: ClubModel

class RelayParticipantModel(BaseModel):
    heat_id: int
    lane_id: int
    club: str
    club_id: int
    relay_event_id: int
    swimmers: List[str]
    time: Optional[str]

    class Config:
        from_attributes = True

class RelaySubmission(BaseModel):
    relay_event_id: int
    time: str

class AssignSwimmerRequest(BaseModel):
    swimmer_id: int  # ID of the swimmer being assigned
    event_id: int  # ID of the event
    heat_id: int  # ID of the heat where the swimmer will be assigned
    lane_id: int  # Lane number where the swimmer will be placed

    class Config:
        orm_mode = True  # Allows compatibility with SQLAlchemy ORM objects

class UpdateFinalTimeRequest(BaseModel):
    event_id: int
    swimmer_event_id: int
    time: str

class RelayEventAssociation(Base):
    __tablename__ = "relay_event_associations"

    id = Column(Integer, primary_key=True)
    relay_event_id = Column(Integer, ForeignKey("relay_events.id"))
    event_id = Column(Integer, ForeignKey("events.id"))

    relay_event = relationship("RelayEvent", backref="associations")
    event = relationship("Event", backref="associations")
# Resolve forward reference
EventModel.update_forward_refs()
