from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from database import engine, SessionLocal
from models import Base, Swimmer, Event, SwimmerEvent, SwimmerModel, EventModel, SwimmerEventModel, UpdateTimeRequest, UpdateLaneOrder, SwimmerUpdateModel
from pydantic import BaseModel
from typing import List, Optional
from fastapi.encoders import jsonable_encoder
from utils import convert_time_to_total_ms, format_date, lane_order, MEDAL_POINTS
from datetime import datetime
import os
import logging
from collections import defaultdict

logging.basicConfig(level=logging.DEBUG)

EVENTS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'events.json')

router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.filters['format_date'] = format_date

# Create database tables
Base.metadata.create_all(bind=engine)

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class SwimmerCreateRequest(BaseModel):
    name: str
    dob: str
    age_group: int
    gender: str
    club: str
    sfi_id: Optional[str]
    event_id: List[int]

@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        swimmers = db.query(Swimmer).all()
        events = db.query(Event).all()
        return templates.TemplateResponse("home.html", {"request": request, "swimmers": swimmers, "events": events})
    except Exception as e:
        logging.error(f"Error loading home page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/", response_class=HTMLResponse)
async def add_swimmer(
    request: Request,
    swimmer_data: SwimmerCreateRequest,
    db: Session = Depends(get_db)
):
    try:
        logging.info(swimmer_data.dob)
        dob_date = datetime.strptime(swimmer_data.dob, "%Y-%m-%d")
        new_swimmer = Swimmer(
            name=swimmer_data.name,
            dob=dob_date,
            age_group=swimmer_data.age_group,
            gender=swimmer_data.gender,
            club=swimmer_data.club,
            sfi_id=swimmer_data.sfi_id
        )
        db.add(new_swimmer)
        db.commit()
        
        for eid in swimmer_data.event_id:
            # Determine the next available heat_id and lane_id
            participant_count = db.query(SwimmerEvent).filter(SwimmerEvent.event_id == eid).count()
            next_lane_index = (participant_count%8)
            next_lane_id = lane_order[next_lane_index]
            next_heat_id = (participant_count // 8) + 1

            new_event_association = SwimmerEvent(
                swimmer_id=new_swimmer.id,
                event_id=eid,
                heat_id=next_heat_id,
                lane_id=next_lane_id
            )
            db.add(new_event_association)
        db.commit()

        swimmers = db.query(Swimmer).all()
        events = db.query(Event).all()
        logging.debug(f"Swimmers loaded: {swimmers}")
        return templates.TemplateResponse("home.html", {"request": request, "swimmers": swimmers, "events": events})
    except Exception as e:
        logging.error(f"Error adding swimmer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=List[EventModel])
def get_events(age_group: Optional[int] = Query(None), gender: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if gender:
        events = db.query(Event).filter(Event.age_group == age_group).filter(Event.gender == gender.lower()).all()
    else:
        events = db.query(Event).all()
    return events

@router.get("/swimmers", response_model=List[SwimmerModel])
def get_swimmers(
    name: Optional[str] = Query(None),
    age_group: Optional[int] = Query(None),
    gender: Optional[str] = Query(None),
    event: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Swimmer).options(joinedload(Swimmer.events).joinedload(SwimmerEvent.event))

    if name:
        query = query.filter(Swimmer.name.ilike(f"%{name}%"))
    if age_group:
        query = query.filter(Swimmer.age_group == age_group)
    if gender:
        query = query.filter(Swimmer.gender == gender)
    if event:
        query = query.join(SwimmerEvent).join(Event).filter(Event.name.ilike(f"%{event}%"))

    swimmers = query.all()
    return JSONResponse(content=jsonable_encoder(swimmers))

@router.put("/update_swimmer/{swimmer_id}", response_model=SwimmerUpdateModel)
async def update_swimmer(swimmer_data: SwimmerModel, db: Session = Depends(get_db)):
    swimmer_id = swimmer_data.id
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Swimmer not found")
    
    dob_date = datetime.strptime(swimmer_data.dob, "%Y-%m-%d")
    swimmer.name = swimmer_data.name
    swimmer.dob = dob_date
    swimmer.age_group = swimmer_data.age_group
    swimmer.gender = swimmer_data.gender
    swimmer.sfi_id = swimmer_data.sfi_id
    swimmer.club = swimmer_data.club
    
    db.commit()
    db.refresh(swimmer)
    return SwimmerModel.model_validate(swimmer)

@router.delete("/swimmers/{swimmer_id}", response_class=JSONResponse)
async def delete_swimmer(swimmer_id: int, db: Session = Depends(get_db)):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Swimmer not found")

    # Delete the swimmer's events first
    db.query(SwimmerEvent).filter(SwimmerEvent.swimmer_id == swimmer_id).delete()

    # Delete the swimmer
    db.delete(swimmer)
    db.commit()
    return {"message": "Swimmer deleted successfully"}

@router.get("/view_swimmers", response_class=HTMLResponse)
async def view_swimmers(
    request: Request,
    db: Session = Depends(get_db),
    search_name: Optional[str] = Query(None),
    age_group: Optional[int] = Query(None),
    gender: Optional[str] = Query(None),
    event_name: Optional[str] = Query(None)
):
    query = db.query(Swimmer).options(joinedload(Swimmer.events).joinedload(SwimmerEvent.event))

    if search_name:
        query = query.filter(Swimmer.name.ilike(f"%{search_name}%"))
    if age_group:
        query = query.filter(Swimmer.age_group == age_group)
    if gender:
        query = query.filter(Swimmer.gender == gender)
    if event_name:
        query = query.join(SwimmerEvent).join(Event).filter(Event.name.ilike(f"%{event_name}%"))

    swimmers = query.all()
    events = db.query(Event).all()

    return templates.TemplateResponse("view_swimmers.html", {"request": request, "swimmers": swimmers, "events": events})


@router.get("/competition")
async def competition(
    request: Request,
    db: Session = Depends(get_db)
):
    return templates.TemplateResponse("competition.html", {"request": request})

@router.get("/competition_data")
async def competition_data(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    event_data = []
    for event in events:
        participant_count = db.query(SwimmerEvent).filter(SwimmerEvent.event_id == event.id).count()
        event_data.append({
            "id": event.id,
            "name": event.name,
            "age_group": event.age_group,
            "gender": event.gender,
            "participant_count": participant_count
        })
    return JSONResponse(content=event_data)


@router.get("/event_participants", response_model=List[SwimmerEventModel])
async def get_event_participants(event_id: int, db: Session = Depends(get_db)):
    participants = db.query(SwimmerEvent).filter(SwimmerEvent.event_id == event_id).order_by(SwimmerEvent.heat_id, SwimmerEvent.lane_id).all()
    return participants

@router.post("/update_lane")
async def update_lane(request: UpdateLaneOrder, db: Session = Depends(get_db)):
    swimmer_event = db.query(SwimmerEvent).filter(SwimmerEvent.id == int(request.swimmer_event_id)).first()
    if not swimmer_event:
        raise HTTPException(status_code=404, detail="SwimmerEvent not found")
    swimmer_event.lane_id = request.lane_id
    swimmer_event.heat_id = int(request.heat_id)
    # if not swimmer_event.heat_id:
    #     swimmer_event.heat_id = 1
    # else:
    #     swimmer_event.heat_id = request.heat_id
    db.commit()
    return {"message": "Lane updated successfully"}

@router.post("/update_times")
async def update_times(request: List[UpdateTimeRequest], db: Session = Depends(get_db)):
    try:
        for update in request:
            swimmer_event = db.query(SwimmerEvent).filter(SwimmerEvent.id == update.swimmer_event_id).first()
            if swimmer_event:
                if update.time == "::":
                    swimmer_event.time = None
                else:
                    swimmer_event.time = update.time
        db.commit()
        return JSONResponse(content={"message": "Times updated successfully"})
    except Exception as e:
        logging.error(f"Error updating times: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recalculate_heats_lanes/{event_id}")
async def recalculate_heats_lanes(event_id: int, db: Session = Depends(get_db)):
    events = db.query(Event).all()

    participants = db.query(SwimmerEvent).filter(SwimmerEvent.event_id == event_id).all()
    if participants:
        # Sort participants by time
        participants.sort(key=lambda x: (x.time is not None, x.time))
        
        # Recalculate heats and lanes
        lane_id = 0
        heat_id = 1
        for participant in participants:
            participant.lane_id = lane_order[lane_id]
            participant.heat_id = heat_id
            lane_id += 1
            if lane_id > 7:
                lane_id = 0
                heat_id += 1

    db.commit()
    return {"message": f"Heats and lanes recalculated for event {event_id}"}

@router.get("/results", response_model=List[EventModel])
async def get_event_results(request: Request, db: Session = Depends(get_db)):
    events = db.query(Event).all()
    event_results = []
    swimmer_points = defaultdict(lambda: defaultdict(int))
    for event in events:
        participants = db.query(SwimmerEvent).filter(SwimmerEvent.event_id == event.id).all()
        # Sort participants by total milliseconds, keeping those without time at the bottom
        # participants = [se for se in participants if se.time is not None]
        participants.sort(key=lambda se: (convert_time_to_total_ms(se.time), se.time is None))
        
        # Assign medals to the top 3 participants
        for i, se in enumerate(participants):
            if i == 0:
                se.medal = 1  # Gold
            elif i == 1:
                se.medal = 2  # Silver
            elif i == 2:
                se.medal = 3  # Bronze
            else:
                break

        if len(participants)>=3:
            for se in participants:
                # Assign points based on medal
                if se.time is not None and se.medal in MEDAL_POINTS:
                    swimmer_points[(se.swimmer.age_group, se.swimmer.gender)][se.swimmer_id] += MEDAL_POINTS[se.medal]

        event_results.append({
            "id": event.id,
            "name": event.name,
            "age_group": event.age_group,
            "gender": event.gender,
            "participants": [
                {
                    "id": se.id,
                    "swimmer_id": se.swimmer_id,
                    "event_id": se.event_id,
                    "medal": se.medal,
                    "time": se.time,
                    "swimmer": {
                        "id": se.swimmer.id,
                        "name": se.swimmer.name,
                        "dob": se.swimmer.dob,
                        "sfi_id": se.swimmer.sfi_id,
                        "age_group": se.swimmer.age_group,
                        "gender": se.swimmer.gender,
                        "club": se.swimmer.club
                    }
                }
                for se in participants
            ]
        })

        # Calculate championship standings for each age group and gender
    championship_standings = {}
    for (age_group, gender), points in swimmer_points.items():
        standings = sorted(points.items(), key=lambda item: item[1], reverse=True)[:5]
        championship_standings[(age_group, gender)] = [
            {
                "swimmer_id": swimmer_id,
                "points": points,
                "swimmer": {
                    "id": db.query(Swimmer).get(swimmer_id).id,
                    "name": db.query(Swimmer).get(swimmer_id).name,
                    "dob": db.query(Swimmer).get(swimmer_id).dob,
                    "sfi_id": db.query(Swimmer).get(swimmer_id).sfi_id,
                    "age_group": db.query(Swimmer).get(swimmer_id).age_group,
                    "gender": db.query(Swimmer).get(swimmer_id).gender,
                    "club": db.query(Swimmer).get(swimmer_id).club
                }
            }
            for swimmer_id, points in standings
        ]

        # Sort championship standings by age group and gender
    sorted_championship_standings = {
        key: championship_standings[key]
        for key in sorted(championship_standings.keys(), key=lambda x: (x[0], x[1]))
    }

    return templates.TemplateResponse("results.html", {"request": request, "results": event_results, "standings": sorted_championship_standings})


