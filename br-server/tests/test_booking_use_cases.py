from app.application.booking_use_cases import BookingUseCases


def test_booking_use_cases_exposes_existing_service_callables():
    use_cases = BookingUseCases()

    assert callable(use_cases.create_booking)
    assert callable(use_cases.cancel_booking)
    assert callable(use_cases.list_bookings)
