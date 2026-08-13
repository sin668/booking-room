import {
  cancelBooking,
  createBooking,
  getBookingPaymentStatus,
  getBookings,
  payBooking,
} from '@/api/bookings'
import { getAvailableCouponsForBooking } from '@/api/coupons'
import { getRoom } from '@/api/rooms'
import { getSeats } from '@/api/seats'
import { getBalance } from '@/api/wallet'

export function fetchBookingsPage(params) {
  return getBookings(params)
}

export function cancelBookingOrder(id) {
  return cancelBooking(id)
}

export function createBookingOrder(payload) {
  return createBooking(payload)
}

export function fetchBookingPaymentStatus(bookingId) {
  return getBookingPaymentStatus(bookingId)
}

export function fetchBookingRoom(roomId) {
  return getRoom(roomId)
}

export function fetchBookingSeats(roomId, params) {
  return getSeats(roomId, params)
}

export function fetchBookingCoupons(payload) {
  return getAvailableCouponsForBooking(payload)
}

export function fetchWalletBalance() {
  return getBalance()
}

export function payPendingBooking(bookingId, paymentMethod) {
  return payBooking(bookingId, paymentMethod)
}
