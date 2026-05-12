from datetime import datetime, timezone, timedelta

def get_colombia_time():
    """Devuelve la fecha y hora actual en la zona horaria de Colombia (UTC-5) como un objeto naive."""
    colombia_tz = timezone(timedelta(hours=-5))
    return datetime.now(colombia_tz).replace(tzinfo=None)
