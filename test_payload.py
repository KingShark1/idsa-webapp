from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models import RelayEvent, Event

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
SQLALCHEMY_DATABASE_URL = "sqlite:///./swimming_competition.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_size=20, max_overflow=0)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def update_relay_events():
    db = SessionLocal()
    try:
        relay_events = db.query(RelayEvent).all()
        for relay_event in relay_events:
            event = db.query(Event).get(relay_event.event_id)
            relay_event.event = event
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_relay_events()
