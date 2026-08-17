from app.models.activity import Activity, ActivityCoupon
from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole, admin_role_menus, admin_user_roles
from app.models.admin_setting import SystemSetting
from app.models.banner import Banner
from app.models.booking import Booking
from app.models.city import City
from app.models.coupon import Coupon, UserCoupon
from app.models.notification import Notification, NotificationPreference, NotificationType
from app.models.room_follow import RoomFollow
from app.models.seat import Seat
from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.user import User
from app.models.user_identity_verification import UserIdentityVerification
from app.models.wallet import WalletTransaction

__all__ = [
    "Activity",
    "ActivityCoupon",
    "AdminMenu",
    "AdminRole",
    "Banner",
    "Booking",
    "City",
    "Course",
    "CourseLesson",
    "Coupon",
    "Notification",
    "NotificationPreference",
    "NotificationType",
    "RoomFollow",
    "Seat",
    "StudyRoom",
    "SystemSetting",
    "Teacher",
    "User",
    "UserIdentityVerification",
    "UserCoupon",
    "WalletTransaction",
    "admin_role_menus",
    "admin_user_roles",
]
