import requests
import time


BASE = "http://localhost:5000"
USER = "tester@local"


def post_sim(payload):
    resp = requests.post(f"{BASE}/internal/voice_simulate", json=payload, timeout=5)
    return resp.json()


def test_demo_booking_listing_and_cancel():
    # 1) Book an event
    booking = {
        "transcript": "Book a meeting tomorrow at 2 PM called Demo Integration",
        "user_id": USER,
        "timezone": "UTC",
        "demo": True,
    }
    r1 = post_sim(booking)
    assert r1.get("ok") is True, f"Booking failed: {r1}"

    # 2) List events for tomorrow - should include our event
    listing = {
        "transcript": "Show my events for tomorrow",
        "user_id": USER,
        "timezone": "UTC",
        "demo": True,
    }
    r2 = post_sim(listing)
    assert r2.get("ok") is True, f"Listing failed: {r2}"
    events = r2.get("events") or []
    assert any("Demo Integration" in (e.get("title") or "") or "Demo" in (e.get("title") or "") for e in events), f"Booked event not found in listing: {events}"

    # 3) Book a second event to cancel later
    booking2 = {
        "transcript": "Schedule Project Sync tomorrow at 4 PM",
        "user_id": USER,
        "timezone": "UTC",
        "demo": True,
    }
    r3 = post_sim(booking2)
    assert r3.get("ok") is True, f"Second booking failed: {r3}"

    # 4) Cancel the Project Sync event (loose matching)
    cancel = {
        "transcript": "Cancel Project Sync tomorrow at 4 PM",
        "user_id": USER,
        "timezone": "UTC",
        "demo": True,
    }
    r4 = post_sim(cancel)
    # Cancellation may return ok True with removed list or ok False with debug - accept either but prefer success
    if not r4.get("ok"):
        # Allow failure if the parser couldn't extract details, but include debug in assertion
        assert False, f"Cancel failed: {r4}"

    # 5) Final listing - Project Sync should no longer be present
    r5 = post_sim(listing)
    assert r5.get("ok") is True, f"Final listing failed: {r5}"
    final_events = r5.get("events") or []
    assert all("Project Sync" not in (e.get("title") or "") for e in final_events), f"Project Sync still present: {final_events}"
