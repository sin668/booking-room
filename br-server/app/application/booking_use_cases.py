from __future__ import annotations

from app.services import booking_service


class BookingUseCases:
    create_booking = staticmethod(booking_service.create_booking)
    list_bookings = staticmethod(booking_service.list_bookings)
    get_booking = staticmethod(booking_service.get_booking)
    cancel_booking = staticmethod(booking_service.cancel_booking)
