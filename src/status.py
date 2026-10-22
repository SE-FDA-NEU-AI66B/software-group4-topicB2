
from datetime import datetime, timedelta


def get_evaluation_status(deadline, completed, now=None):
    """Return the display status for one student's evaluation."""
    if completed:
        return "Completed"

    if isinstance(deadline, str):
        deadline = datetime.fromisoformat(deadline)

    now = now or datetime.now()

    if deadline <= now:
        return "Closed"

    if deadline - now < timedelta(hours=24):
        return "Due soon"

    return "Active"
