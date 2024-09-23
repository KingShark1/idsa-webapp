from fastapi import APIRouter, Request, Depends, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from database import engine, SessionLocal
from models import *
from pydantic import BaseModel
from typing import List, Optional, Union
from fastapi.encoders import jsonable_encoder
from utils import convert_time_to_total_ms, format_date, lane_order, load_json
from datetime import datetime
from sqlalchemy import func
import os
import logging
from collections import defaultdict
import traceback

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
        swimmers = db.query(Swimmer).order_by(Swimmer.id.desc()).first()
        events = db.query(Event).all()
        config = load_json('static/config.json')
        age_group_map = config.get('age_group_map', {})
        return templates.TemplateResponse("home.html", {"request": request, "swimmers": swimmers, "events": events, "age_group_map":age_group_map})
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
        dob_date = datetime.strptime(swimmer_data.dob, "%Y-%m-%d")

        # Fetch the club using the club ID from swimmer_data
        club = db.query(Club).filter(Club.name == swimmer_data.club).first()
        if not club:
            # If the club is not found, try to add the new club
            try:
                club_data = ClubModel(name=swimmer_data.club, total_points=0)  # Assuming total_points starts at 0
                result = create_club(club_data, db)
                if "club" in result:
                    club = result["club"]
                else:
                    raise HTTPException(status_code=400, detail="Something went wrong in adding the new club")
            except HTTPException as e:
                raise e
        new_swimmer = Swimmer(
            name=swimmer_data.name,
            dob=dob_date,
            age_group=swimmer_data.age_group,
            gender=swimmer_data.gender,
            club=club,
            sfi_id=swimmer_data.sfi_id
        )
        db.add(new_swimmer)
        db.commit()

        for eid in swimmer_data.event_id:
            # Fetch the event to check if it's a relay
            event = db.query(Event).filter(Event.id == eid).first()

            if "Relay" in event.name:
                # Handle relay events
                # Check if a RelayEvent already exists for this club and event
                relay_event = db.query(RelayEvent).filter(RelayEvent.club_id == club.id, RelayEvent.event_id == eid).first()
                if not relay_event:
                    participant_count = db.query(RelayEvent).filter(RelayEvent.event_id == event.id).distinct(RelayEvent.club_id).count()
                    next_lane_index = (participant_count % 8)
                    next_lane_id = lane_order[next_lane_index]
                    next_heat_id = (participant_count // 8) + 1

                    # Create a new RelayEvent if one doesn't exist
                    relay_event = RelayEvent(
                        club_id=club.id,
                        event_id=eid,
                        heat_id=next_heat_id,
                        lane_id=next_lane_id
                    )
                    db.add(relay_event)
                    db.commit()  # Commit to get the ID if needed later

                # Add the swimmer to the RelayEvent
                relay_event.swimmers.append(new_swimmer)

            else:
                # Handle regular (non-relay) events
                # Determine the next available heat_id and lane_id
                participant_count = db.query(SwimmerEvent).filter(SwimmerEvent.event_id == eid).count()
                next_lane_index = (participant_count % 8)
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

        events = db.query(Event).all()
        config = load_json('static/config.json')
        return templates.TemplateResponse("home.html", {"request": request, "swimmers": new_swimmer, "events": events, "age_group_map": config.get("age_group_map", {})})
    except Exception as e:
        logging.error(f"Error adding swimmer: {str(traceback.print_exception(e))}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/events", response_model=List[EventModel])
def get_events(age_group: Optional[int] = Query(None), gender: Optional[str] = Query(None), db: Session = Depends(get_db)):
    if gender:
        events = db.query(Event).filter(Event.age_group == age_group).filter(Event.gender == gender.lower()).order_by(Event.name).all()
    else:
        events = db.query(Event).all()

    # Sort events by stroke name (part after 'mt.')
    sorted_events = sorted(events, key=lambda e: e.name.split("mt. ")[-1].strip().lower(), reverse=True)

    return sorted_events

@router.get("/swimmers", response_model=List[SwimmerModel])
def get_swimmers(
    name: Optional[str] = Query(None),
    age_group: Optional[int] = Query(None),
    gender: Optional[str] = Query(None),
    event: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Swimmer).options(
        joinedload(Swimmer.events).joinedload(SwimmerEvent.event),
        joinedload(Swimmer.relay_events).joinedload(RelayEvent.event)
    )

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

@router.put("/update_swimmer/{swimmer_id}", response_class=JSONResponse)
async def update_swimmer(swimmer_id: int, update_data: SwimmerUpdateModel, db: Session = Depends(get_db)):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Swimmer not found")

    # If the gender or age group has changed, delete the swimmer and create a new one
    if swimmer.gender != update_data.gender or swimmer.age_group != update_data.age_group:
        await delete_swimmer(swimmer_id, db)  # Reuse the delete swimmer function

        # Now call the add_swimmer logic with the new data
        new_swimmer_data = SwimmerCreateRequest(
            name=update_data.name,
            dob=update_data.dob,
            age_group=update_data.age_group,
            gender=update_data.gender,
            club=swimmer.club.name,
            event_id=update_data.events
        )
        await add_swimmer(new_swimmer_data, db)

        return {"message": "Swimmer updated with new gender/age group"}


@router.delete("/swimmers/{swimmer_id}", response_class=JSONResponse)
async def delete_swimmer(swimmer_id: int, db: Session = Depends(get_db)):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Swimmer not found")

    # query the events, the swimmer participated in
    swimmer_events = db.query(SwimmerEvent).filter(SwimmerEvent.swimmer_id == swimmer_id).all()
    event_ids = {se.event_id for se in swimmer_events}

    # Delete the swimmer's events
    db.query(SwimmerEvent).filter(SwimmerEvent.swimmer_id == swimmer_id).delete()

    # Delete the swimmer
    db.delete(swimmer)
    db.commit()

    # Recalculate heats and lanes for each event the swimmer participated in
    for event_id in event_ids:
        await recalculate_heats_lanes(event_id, db)

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

@router.get("/swimmers/{swimmer_id}", response_model=SwimmerEventForCompetitionModel)
async def get_swimmer_events(swimmer_id: int, db: Session = Depends(get_db)):
    swimmer = db.query(Swimmer).filter(Swimmer.id == swimmer_id).first()
    if not swimmer:
        raise HTTPException(status_code=404, detail="Swimmer not found")

    # Fetch associated events
    swimmer_events = db.query(SwimmerEvent).filter(SwimmerEvent.swimmer_id == swimmer_id).all()
    event_names = [se.event.name for se in swimmer_events]

    # relay_swimmer_event = db.query(RelayEvent).filter(RelayEvent.swimmer_id == swimmer_id).all()
    # relay_event_names = [se.event.name for se in relay_swimmer_event]
    relay_event_names = []
    logging.info(relay_event_names)
    # Return swimmer details along with the event names
    return {
        "id": swimmer.id,
        "name": swimmer.name,
        "dob": swimmer.dob,
        "age_group": swimmer.age_group,
        "gender": swimmer.gender,
        "club": swimmer.club,
        "events": event_names,
        "relay_events": relay_event_names
    }

@router.delete("/swimmers/{swimmer_id}/events/{event_id}")
async def delete_swimmer_event(swimmer_id: int, event_id: int, db: Session = Depends(get_db)):
    # Fetch the swimmer event
    swimmer_event = db.query(SwimmerEvent).filter(SwimmerEvent.id == event_id).first()
    # Check if the swimmer event exists
    if not swimmer_event:
        raise HTTPException(status_code=404, detail="Event not found for swimmer")
    event_no = swimmer_event.event_id
    # Delete the swimmer event
    db.delete(swimmer_event)
    db.commit()

    # After deletion, recalculate heats and lanes for the event
    await recalculate_heats_lanes(event_no, db)

    return {"message": "Event deleted successfully"}

@router.delete("/swimmers/{swimmer_id}/relay-events/{relay_event_id}")
def delete_relay_event(swimmer_id: int, relay_event_id: int, db: Session = Depends(get_db)):
    relay_event = db.query(RelayEvent).get(relay_event_id)
    if relay_event:
        db.delete(relay_event)
        db.commit()
        return {"message": "Relay event deleted successfully"}
    else:
        return {"message": "Relay event not found"}, 404

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
        if "Relay" in event.name:
            # Count distinct clubs participating in the relay event
            participant_count = db.query(RelayEvent).filter(RelayEvent.event_id == event.id).distinct(RelayEvent.club_id).count()
        else:
            # Count total number of swimmer events for non-relay events
            participant_count = db.query(SwimmerEvent).filter(SwimmerEvent.event_id == event.id).count()
        event_data.append({
            "id": event.id,
            "name": event.name,
            "age_group": event.age_group,
            "gender": event.gender,
            "participant_count": participant_count,
            "time_trial": event.time_trial
        })
    return JSONResponse(content=event_data)


@router.get("/eligible_swimmers")
async def get_eligible_swimmers(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Fetch swimmers eligible for the event based on age group and gender
    eligible_swimmers = db.query(Swimmer).filter(
        Swimmer.age_group == event.age_group,
        Swimmer.gender ==str.capitalize(event.gender),

    ).all()
    print(eligible_swimmers)
    # Return swimmer data as JSON
    return [{"id": swimmer.id, "name": swimmer.name, "dob": swimmer.dob, "club": {"name": swimmer.club.name}} for swimmer in eligible_swimmers]

@router.post("/assign_swimmer_to_event")
async def assign_swimmer_to_event(data: AssignSwimmerRequest, db: Session = Depends(get_db)):
    # Check if the swimmer is already in the event
    existing_participation = db.query(SwimmerEvent).filter(
        SwimmerEvent.swimmer_id == data.swimmer_id,
        SwimmerEvent.event_id == data.event_id
    ).first()

    if existing_participation:
        raise HTTPException(status_code=400, detail="Swimmer is already participating in this event")

    # Assign swimmer to event
    new_participation = SwimmerEvent(
        swimmer_id=data.swimmer_id,
        event_id=data.event_id,
        heat_id=data.heat_id,
        lane_id=data.lane_id
    )
    db.add(new_participation)
    db.commit()

    return {"message": "Swimmer successfully assigned to event"}


@router.get("/event_participants", response_model=Union[List[SwimmerEventModel], List[RelayParticipantModel]])
async def get_event_participants(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()

    if "Relay" in event.name:
        # Fetch all relay events for the given event_id
        relay_events = db.query(RelayEvent).filter(RelayEvent.event_id == event_id).all()

        relay_participants = []
        for relay_event in relay_events:
            club_id = relay_event.club_id

            # Collect swimmer names associated with this relay event
            swimmer_names = [swimmer.name for swimmer in relay_event.swimmers]

            # Create a RelayParticipantModel entry for each relay event
            relay_participants.append(RelayParticipantModel(
                heat_id=relay_event.heat_id,  # Assuming heat_id isn't used in relay context or needs to be handled differently
                lane_id=relay_event.lane_id,  # Similarly, handle lane_id as per your actual logic
                club=relay_event.club.name,
                club_id=club_id,
                swimmers=swimmer_names,
                time=relay_event.time,
                relay_event_id=relay_event.id
            ))

        logging.info(relay_participants)
        return relay_participants

    else:
        # For non-relay events, fetch participants as before
        participants = db.query(SwimmerEvent).filter(SwimmerEvent.event_id == event_id).order_by(SwimmerEvent.heat_id, SwimmerEvent.lane_id).all()
        return participants

# New route to fetch top 8 participants for a given event
@router.get("/top_8_participants", response_model=List[Union[SwimmerEventModel, RelayParticipantModel]])
async def get_top_8_participants(event_id: int, db: Session = Depends(get_db)):
    try:
        # Query to fetch top 8 participants sorted by their times
        participants = (db.query(SwimmerEvent)
                        .filter(SwimmerEvent.event_id == event_id)
                        .order_by(SwimmerEvent.time.asc())  # Sort by time in ascending order (best to worst)
                        .limit(8)  # Limit to the top 8 participants
                        .all())

        return participants

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
async def update_times(request: List[Union[UpdateSwimmerTimeRequest, UpdateRelayTimeRequest]], db: Session = Depends(get_db)):
    try:
        for update in request:
            logging.info(update)

            if isinstance(update, UpdateRelayTimeRequest):
                # Update time for a relay event
                relay_event = db.query(RelayEvent).filter(RelayEvent.id == update.relay_event_id).first()
                if relay_event:
                    if update.time == "::":
                        relay_event.time = None
                    else:
                        relay_event.time = update.time
                    logging.info(f"Updated RelayEvent: {relay_event.time}, Club: {relay_event.club.name}, Event ID: {relay_event.event_id}")
            else:
                # Update time for a regular swimmer event
                swimmer_event = db.query(SwimmerEvent).filter(SwimmerEvent.id == update.swimmer_event_id).first()
                if swimmer_event:
                    if update.time == "::":
                        swimmer_event.time = None
                    else:
                        swimmer_event.time = update.time
                    logging.info(f"Updated SwimmerEvent: {swimmer_event.time}, Swimmer: {swimmer_event.swimmer.name}, Event ID: {swimmer_event.event_id}")

        db.commit()
        return JSONResponse(content={"message": "Times updated successfully"})
    except Exception as e:
        logging.error(f"Error updating times: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update_final_times")
async def update_final_times(request: List[UpdateFinalTimeRequest], db: Session = Depends(get_db)):
    try:
        for update in request:
            logging.info(update)

            # Check if the event is a final event
            swimmer_event = db.query(SwimmerEvent).filter(SwimmerEvent.id == update.swimmer_event_id).first()
            swimmer = swimmer_event.swimmer
            event = db.query(Event).filter(Event.id == update.event_id).first()
            if event and event.time_trial is False:
                # Update final time for a swimmer event
                final_event = db.query(FinalEvent).filter(FinalEvent.event_id == update.event_id, FinalEvent.swimmer_id == swimmer.id).first()
                if final_event:
                    if update.time == "::":
                        final_event.time = None
                    else:
                        final_event.time = update.time
                    logging.info(final_event.swimmer)
                    logging.info(f"Updated FinalEvent: {final_event.time}, Swimmer: {final_event.swimmer.name}, Event ID: {final_event.event_id}")
                else:
                    logging.info("Final event not found, creating new one.")
                    # Create a new FinalEvent record if it doesn't exist
                    logging.info(update.swimmer_event_id)
                    swimmer_event = db.query(SwimmerEvent).get(update.swimmer_event_id)
                    swimmer = swimmer_event.swimmer
                    logging.info(swimmer)
                    event = db.query(Event).get(update.event_id)
                    if update.time == "::":
                        time = None
                    else:
                        time = update.time
                    final_event = FinalEvent(
                        event_id=event.id,
                        swimmer_id=swimmer.id,
                        time=time,
                        swimmer=swimmer,
                        event=event
                    )
                    db.add(final_event)
                    logging.info(f"Created FinalEvent: {final_event.time}, Swimmer: {final_event.swimmer.name}, Event ID: {final_event.event_id}")

        db.commit()
        return JSONResponse(content={"message": "Final times updated successfully"})
    except Exception as e:
        logging.info(traceback.print_exc())
        logging.error(f"Error updating final times: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

"""
@router.post("/relay_submission_event")
async def relay_submission_event(request: List[RelaySubmission], db: Session = Depends(get_db)):
    try:
        logging.info(request)
        for submission in request:
            relay_event = RelayEvent(event_id=submission.relay_event_id, time=submission.time)
            db.add(relay_event)
        db.commit()
        return {"message": "Relay event times submitted successfully"}
    except Exception as e:
        logging.error(f"Error submitting relay times: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
"""
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
    config = load_json("static/config.json")
    db.query(Club).update({Club.total_points: 0})
    db.commit()

    for event in events:
        if "Relay" in event.name:
            participants = db.query(RelayEvent).filter(RelayEvent.event_id == event.id).all()
            participants.sort(key=lambda se: (convert_time_to_total_ms(se, se.time), se.time is None))
            relay_participants = []
            for i, se in enumerate(participants):
                if i <= config["min_participants_for_relay_points"]:
                    se.medal = str(i+1)


            if len(participants) > 2:
                if participants[2].time != "99:99:99" or participant[2].time != "88:88:88":
                    for se in participants:
                        club = se.club

                        if se.time is not None and f"{se.medal}" in config["relay_medal_points"]:
                            # Find the Club
                            # Add point to the club
                            club.total_points += config["relay_medal_points"][f"{se.medal}"]
                            db.commit()
            for participant in participants:
                club_id = participant.club_id
                swimmer_names = [swimmer.name for swimmer in participant.swimmers]
                relay_participants.append({
                    "id": participant.id,
                    "club_id": club_id,
                    "club_name": participant.club.name,
                    "swimmers": swimmer_names,
                    "time": participant.time
                })

            event_results.append({
                "id": event.id,
                "name": event.name,
                "age_group": event.age_group,
                "gender": event.gender,
                "relay": True,
                "participants": relay_participants
            })

        else:
            if event.time_trial:
                participants = db.query(SwimmerEvent).filter(SwimmerEvent.event_id == event.id).all()
                participants.sort(key=lambda se: (convert_time_to_total_ms(se, se.time), se.time is None))
            else:

                participants = db.query(FinalEvent).filter(FinalEvent.event_id == event.id).all()
                # Sort participants by total milliseconds, keeping those without time at the bottom
                # participants = [se for se in participants if se.time is not None]

                participants.sort(key=lambda se: (convert_time_to_total_ms(se, se.time), se.time is None))


            # Assign medals to the top n participants, configured in the config.json
            for i, se in enumerate(participants):
                if i <= config["min_participants_for_points"]:
                    se.medal = str(i+1)  # Gold

            if len(participants) > 2:
                # Check if the 3rd person is not absent or DNF
                if participants[2].time != "99:99:99" or participants[2].time != "88:88:88":
                    for se in participants:
                        # Assign points based on medal
                        if se.time is not None and f"{se.medal}" in config["medal_points"]:
                            swimmer_points[(se.swimmer.age_group, se.swimmer.gender)][se.swimmer_id] += config["medal_points"][f"{se.medal}"]
                            # Fetch Swimmer's club
                            se.swimmer.club.total_points += config["medal_points"][f"{se.medal}"]
                            db.commit()

            event_results.append({
                "id": event.id,
                "name": event.name,
                "age_group": event.age_group,
                "gender": event.gender,
                "relay": False,
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
                    "club": db.query(Swimmer).get(swimmer_id).club.name
                }
            }
            for swimmer_id, points in standings
        ]

        # Sort championship standings by age group and gender
    sorted_championship_standings = {
        key: championship_standings[key]
        for key in sorted(championship_standings.keys(), key=lambda x: (x[0], x[1]))
    }

    sorted_club_standings = db.query(Club).order_by(Club.total_points.desc()).all()

    return templates.TemplateResponse("results.html", {"request": request, "results": event_results, "standings": sorted_championship_standings, "club_standings": sorted_club_standings})

@router.post('/create_club')
def create_club(club_data: ClubModel, db: Session = Depends(get_db)):
    try:
        # Check if the club already exists
        existing_club = db.query(Club).filter_by(name=club_data.name).first()
        if existing_club:
            return {"message": "Club already exists", "club": existing_club}

        # Create a new club if it doesn't exist
        new_club = Club(name=club_data.name, total_points=club_data.total_points)
        db.add(new_club)
        db.commit()
        db.refresh(new_club)
        return {"message": "Club added successfully", "club": new_club}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
