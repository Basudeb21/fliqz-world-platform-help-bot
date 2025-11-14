# state.py (shared global memory)

ticket_state = {
    "is_ticket_generated": 0,
    "ticket_step": None,
    "data": {
        "category": None,
        "subject": None,
        "description": None
    }
}
