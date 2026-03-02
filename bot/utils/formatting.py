from datetime import datetime


def format_dt(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y %H:%M")
