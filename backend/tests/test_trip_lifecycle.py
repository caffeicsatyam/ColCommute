from __future__ import annotations

import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from colcommute.db import session as db_session
from colcommute.db.base import Base
from colcommute.db.models import Trip, TripFeedback, TripPayment, User
from services import ride_services


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def setup_function() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db_session._engine = engine
    db_session._session_factory = TestingSessionLocal

    session = TestingSessionLocal()
    session.add_all(
        [
            User(external_user_id="offer_user"),
            User(external_user_id="need_user"),
        ]
    )
    session.commit()
    session.close()


def _create_confirmed_trip() -> str:
    offer = ride_services.register_commute_post(
        user_id="offer_user",
        origin="Sector 52 metro, Noida",
        destination="NIET Greater Noida",
        destination_place_id="dest-3",
        destination_lat=1.0,
        destination_lng=2.0,
        destination_label="NIET Greater Noida",
        time_bucket="morning",
        vacant_seats=3,
        origin_place_id="origin-offer",
        origin_label="Sector 52 metro, Noida",
    )
    need = ride_services.register_commute_post(
        user_id="need_user",
        origin="Sector 73, Noida",
        destination="NIET Greater Noida",
        destination_place_id="dest-3",
        destination_lat=1.0,
        destination_lng=2.0,
        destination_label="NIET Greater Noida",
        time_bucket="morning",
        seats_needed=1,
        origin_place_id="origin-need",
        origin_label="Sector 73, Noida",
    )
    trip = ride_services.confirm_trip(
        offer["commute_post"]["commute_post_id"],
        need["commute_post"]["commute_post_id"],
    )
    return trip["trip"]["trip_id"]


def test_commute_post_preserves_user_facing_text() -> None:
    result = ride_services.register_commute_post(
        user_id="offer_user",
        origin="Sector 52 Metro, Noida",
        destination="NIET Greater Noida",
        destination_place_id="dest-4",
        destination_lat=1.0,
        destination_lng=2.0,
        destination_label="NIET Greater Noida",
        time_bucket="morning",
        vacant_seats=3,
        origin_place_id="origin-4",
        origin_label="Sector 52 Metro, Noida",
    )

    assert result["status"] == "success"
    assert result["commute_post"]["origin"] == "Sector 52 Metro, Noida"
    assert result["commute_post"]["destination"] == "NIET Greater Noida"


def test_trip_lifecycle_and_payment_persist() -> None:
    trip_id = _create_confirmed_trip()

    started = ride_services.start_trip(trip_id)
    completed = ride_services.complete_trip(trip_id)
    paid = ride_services.process_trip_payment(trip_id, ["offer_user", "need_user"], 200)

    session = TestingSessionLocal()
    parsed_trip_id = uuid.UUID(trip_id)
    trip = session.get(Trip, parsed_trip_id)
    payments = session.query(TripPayment).filter_by(trip_id=parsed_trip_id).all()
    session.close()

    assert started["status"] == "success"
    assert completed["status"] == "success"
    assert paid["status"] == "success"
    assert trip.status == "paid"
    assert len(payments) == 2


def test_feedback_persists() -> None:
    trip_id = _create_confirmed_trip()
    ride_services.complete_trip(trip_id)

    result = ride_services.log_trip_feedback(
        ride_id=trip_id,
        user_id="need_user",
        feedback_score=5,
        feedback_text="Smooth ride",
    )

    session = TestingSessionLocal()
    feedback = session.query(TripFeedback).filter_by(trip_id=uuid.UUID(trip_id)).one()
    session.close()

    assert result["status"] == "success"
    assert feedback.feedback_text == "Smooth ride"
