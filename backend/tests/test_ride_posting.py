from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from colcommute.db.base import Base
from colcommute.db.models import User
from colcommute.db import session as db_session
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
            User(external_user_id="mixed_user"),
        ]
    )
    session.commit()
    session.close()


def test_same_user_can_have_offer_and_need_for_same_time_if_post_type_differs() -> None:
    first = ride_services.register_commute_post(
        user_id="mixed_user",
        origin="ABES College",
        destination="JSS Noida",
        destination_place_id="dest-1",
        destination_lat=1.0,
        destination_lng=2.0,
        destination_label="JSS Noida",
        time_bucket="evening",
        seats_needed=1,
    )
    second = ride_services.register_commute_post(
        user_id="mixed_user",
        origin="ABES College",
        destination="JSS Noida",
        destination_place_id="dest-1",
        destination_lat=1.0,
        destination_lng=2.0,
        destination_label="JSS Noida",
        time_bucket="evening",
        vacant_seats=2,
    )

    assert first["status"] == "success"
    assert second["status"] == "success"
    assert second["commute_post"]["vacant_seats"] == 2
    assert second["commute_post"]["seats_needed"] == 0


def test_duplicate_offer_same_route_and_time_is_rejected() -> None:
    first = ride_services.register_commute_post(
        user_id="offer_user",
        origin="Meerut",
        destination="ABESIT Ghaziabad",
        destination_place_id="dest-2",
        destination_lat=1.0,
        destination_lng=2.0,
        destination_label="ABESIT Ghaziabad",
        time_bucket="morning",
        vacant_seats=3,
    )
    second = ride_services.register_commute_post(
        user_id="offer_user",
        origin="Meerut",
        destination="ABESIT Ghaziabad",
        destination_place_id="dest-2",
        destination_lat=1.0,
        destination_lng=2.0,
        destination_label="ABESIT Ghaziabad",
        time_bucket="morning",
        vacant_seats=1,
    )

    assert first["status"] == "success"
    assert second["status"] == "error"
    assert "already have a offer post" in second["error_message"]


def test_find_matches_pairs_offer_with_need() -> None:
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
    )

    match_result = ride_services.find_matches_for_commute_post(
        offer["commute_post"]["commute_post_id"]
    )

    assert offer["status"] == "success"
    assert need["status"] == "success"
    assert match_result["status"] == "success"
    assert match_result["match_count"] == 1
    assert match_result["matches"][0]["relationship"] == "your_offer_their_need"


def test_find_matches_when_rider_is_in_middle_of_offer_route() -> None:
    offer = ride_services.register_commute_post(
        user_id="offer_user",
        origin="Upstream Point",
        destination="NIET Greater Noida",
        destination_place_id="dest-4",
        destination_lat=28.5000,
        destination_lng=77.5000,
        destination_label="NIET Greater Noida",
        time_bucket="morning",
        vacant_seats=3,
        origin_place_id="origin-upstream",
        origin_lat=28.7000,
        origin_lng=77.3000,
        origin_label="Upstream Point",
    )
    need = ride_services.register_commute_post(
        user_id="need_user",
        origin="Middle Point",
        destination="NIET Greater Noida",
        destination_place_id="dest-4",
        destination_lat=28.5000,
        destination_lng=77.5000,
        destination_label="NIET Greater Noida",
        time_bucket="morning",
        seats_needed=1,
        origin_place_id="origin-middle",
        origin_lat=28.6000,
        origin_lng=77.4000,
        origin_label="Middle Point",
    )

    match_result = ride_services.find_matches_for_commute_post(
        need["commute_post"]["commute_post_id"]
    )

    assert offer["status"] == "success"
    assert need["status"] == "success"
    assert match_result["status"] == "success"
    assert match_result["match_count"] == 1
    assert match_result["matches"][0]["relationship"] == "their_offer_your_need"


def test_route_search_falls_back_to_nearby_requests_when_no_offers_exist() -> None:
    need = ride_services.register_commute_post(
        user_id="need_user",
        origin="Ghaziabad",
        destination="JSS Noida",
        destination_place_id="dest-5",
        destination_lat=28.6157,
        destination_lng=77.3592,
        destination_label="JSS Noida",
        time_bucket="evening",
        seats_needed=1,
        origin_place_id="origin-ghaziabad",
        origin_lat=28.6692,
        origin_lng=77.4538,
        origin_label="Ghaziabad",
    )

    result = ride_services.search_commute_posts_for_route(
        origin_place_id="origin-ghaziabad",
        origin_lat=28.6692,
        origin_lng=77.4538,
        destination_place_id="dest-5",
        destination_lat=28.6157,
        destination_lng=77.3592,
        time_bucket="evening",
        post_kind="offer",
    )

    assert need["status"] == "success"
    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["alternate_post_kind"] == "need"
    assert result["alternate_count"] == 1
    assert result["alternate_commute_posts"][0]["post_kind"] == "need"


def test_route_match_for_lal_kuan_to_abesit_to_noida() -> None:
    offer = ride_services.register_commute_post(
        user_id="offer_user",
        origin="Lal Kuan",
        destination="Noida",
        destination_place_id="dest-noida",
        destination_lat=28.5700,
        destination_lng=77.3200,
        destination_label="Noida",
        time_bucket="morning",
        vacant_seats=2,
        origin_place_id="origin-lal-kuan",
        origin_lat=28.6400,
        origin_lng=77.4600,
        origin_label="Lal Kuan, Ghaziabad",
    )

    result = ride_services.search_commute_posts_for_route(
        origin_text="ABESIT",
        origin_place_id="origin-abesit",
        origin_lat=28.6320,
        origin_lng=77.4480,
        destination_text="Noida",
        destination_place_id="dest-noida",
        destination_lat=28.5700,
        destination_lng=77.3200,
        time_bucket="morning",
        post_kind="offer",
    )

    assert offer["status"] == "success"
    assert result["status"] == "success"
    assert result["count"] == 1
    assert result["commute_posts"][0]["post_kind"] == "offer"
    assert result["commute_posts"][0]["origin"] == "Lal Kuan, Ghaziabad"
