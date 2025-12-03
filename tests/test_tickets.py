from db import (
    create_ticket,
    list_tickets,
    get_ticket,
    update_ticket_status,
)

def test_create_bug_ticket():
    tid = create_ticket(
        ticket_type="Bug",
        subject="App crashes",
        summary="Crash on login",
        prerequisites="None",
        steps_to_replicate="1. Open app\n2. Login\n3. Boom",
        outcome="Crash",
        expected_outcome="Should not crash",
        created_by="alice",
    )

    ticket = get_ticket(tid)
    assert ticket is not None
    assert ticket["ticket_type"] == "Bug"
    assert ticket["status"] == "New"
    assert ticket["subject"] == "App crashes"

def test_create_test_case_ticket():
    tid = create_ticket(
        ticket_type="Test Case",
        subject="Verify login workflow",
        summary="",                 # ignored for test case
        prerequisites="User exists",
        steps_to_replicate="1. Enter credentials\n2. Click login",
        outcome="",                 # ignored for test case
        expected_outcome="Login should succeed",
        created_by="tester",
        user_id=None,
        parent_id=None,
    )

    ticket = get_ticket(tid)
    assert ticket["ticket_type"] == "Test Case"
    assert ticket["expected_outcome"] == "Login should succeed"

def test_list_tickets_filters_and_search():
    # Add multiple tickets
    create_ticket("Bug", "Crash", "sum", "pre", "steps", "out", "exp", "alice")
    create_ticket("Bug", "Login fails", "s", "p", "s", "o", "e", "bob")
    create_ticket("Test Case", "Verify logout", "", "p", "s", "", "e", "alice")

    all_tickets = list_tickets()
    assert len(all_tickets) == 3

    search_results = list_tickets(search="login")
    assert len(search_results) == 1
    assert search_results[0]["subject"].lower().startswith("login")

def test_update_ticket_status():
    tid = create_ticket(
        "Bug", "Crash", "sum", "pre", "steps", "out", "exp", "alice"
    )

    update_ticket_status(tid, "In Progress")
    t = get_ticket(tid)

    assert t["status"] == "In Progress"