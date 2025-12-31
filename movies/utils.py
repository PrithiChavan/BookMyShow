from django.utils import timezone
from datetime import timedelta
from .models import Seat

RESERVATION_TIME = 5  

def release_expired_seats():
    expiry_time = timezone.now() - timedelta(minutes=RESERVATION_TIME)

    expired_seats = Seat.objects.filter(
        is_reserved=True,
        is_booked=False,
        reserved_at__lt=expiry_time
    )

    for seat in expired_seats:
        seat.is_reserved = False
        seat.reserved_at = None
        seat.save()
