"""Tencent Cloud IM Server REST API integration for user account sync.

This service handles server-side IM operations:
- account_import: Create IM user account
- account_delete: Delete IM user account
- profile_set: Update user profile (nickname, avatar)

Documentation: https://cloud.tencent.com/document/product/269/1611
"""

import logging
import random
from typing import Optional

import httpx

from app.core.config import settings
from app.core.im import gen_user_sig

logger = logging.getLogger(__name__)

IM_REST_API_BASE = settings.IM_REST_API_BASE_URL


class IMSyncService:
    """Sync user accounts with Tencent Cloud IM Server."""

    @staticmethod
    def _is_configured() -> bool:
        """Check if IM server-side sync is configured."""
        return bool(
            settings.IM_SDK_APP_ID
            and settings.IM_SERVER_KEY
            and settings.IM_ADMIN_USER
        )

    @staticmethod
    def _build_url(service: str, command: str) -> str:
        """Build authenticated REST API URL.

        Args:
            service: API service name (e.g., "im_open_login_svc")
            command: API command name (e.g., "account_import")

        Returns:
            Full URL with authentication parameters
        """
        admin_user = settings.IM_ADMIN_USER
        admin_sig = gen_user_sig(admin_user)
        random_int = random.randint(1, 2**32 - 1)

        return (
            f"{IM_REST_API_BASE}/{service}/{command}"
            f"?sdkappid={settings.IM_SDK_APP_ID}"
            f"&identifier={admin_user}"
            f"&usersig={admin_sig}"
            f"&random={random_int}"
            f"&contenttype=json"
        )

    @staticmethod
    async def import_account(
        user_id: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> bool:
        """Import (create) a user account in Tencent IM.

        Args:
            user_id: The IM user ID (derived from users.id, see app.core.im.to_im_user_id)
            nickname: Optional nickname to set
            avatar_url: Optional avatar URL to set

        Returns:
            True if successful, False otherwise
        """
        if not IMSyncService._is_configured():
            logger.debug("IM server-side sync not configured, skipping account_import")
            return False

        # Validate user_id format (Tencent IM restriction)
        if not user_id or len(user_id.encode("utf-8")) > 32:
            logger.warning(f"IM account_import skipped for {user_id}: user_id too long or empty")
            return False

        url = IMSyncService._build_url("im_open_login_svc", "account_import")

        payload = {"UserID": user_id}
        if nickname and nickname.strip() and len(nickname.encode("utf-8")) <= 500:
            payload["Nick"] = nickname
        if avatar_url and avatar_url.startswith(("http://", "https://")):
            payload["FaceUrl"] = avatar_url

        logger.info(
            f"IM account_import request for {user_id}: "
            f"Nick={payload.get('Nick')}, FaceUrl={bool(payload.get('FaceUrl'))}"
        )

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                action_status = data.get("ActionStatus")
                error_code = data.get("ErrorCode")

                if action_status == "OK" and error_code == 0:
                    logger.info(f"IM account imported: {user_id}")
                    return True
                else:
                    error_info = data.get("ErrorInfo", "")
                    logger.warning(
                        f"IM account_import failed for {user_id}: "
                        f"ErrorCode={error_code}, ErrorInfo={error_info}"
                    )
                    return False

        except httpx.HTTPError as e:
            logger.error(f"IM account_import HTTP error for {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"IM account_import unexpected error for {user_id}: {e}")
            return False

    @staticmethod
    async def delete_account(user_id: str) -> bool:
        """Delete a user account from Tencent IM.

        Args:
            user_id: The IM user ID to delete

        Returns:
            True if successful, False otherwise
        """
        if not IMSyncService._is_configured():
            logger.debug("IM server-side sync not configured, skipping account_delete")
            return False

        url = IMSyncService._build_url("im_open_login_svc", "account_delete")

        payload = {"DeleteItem": [{"UserID": user_id}]}

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                action_status = data.get("ActionStatus")
                error_code = data.get("ErrorCode")

                if action_status == "OK" and error_code == 0:
                    logger.info(f"IM account deleted: {user_id}")
                    return True
                else:
                    error_info = data.get("ErrorInfo", "")
                    logger.warning(
                        f"IM account_delete failed for {user_id}: "
                        f"ErrorCode={error_code}, ErrorInfo={error_info}"
                    )
                    return False

        except httpx.HTTPError as e:
            logger.error(f"IM account_delete HTTP error for {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"IM account_delete unexpected error for {user_id}: {e}")
            return False

    @staticmethod
    async def set_profile(
        user_id: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> bool:
        """Update a user's profile in Tencent IM.

        Args:
            user_id: The IM user ID
            nickname: Optional new nickname
            avatar_url: Optional new avatar URL

        Returns:
            True if successful, False otherwise
        """
        if not IMSyncService._is_configured():
            logger.debug("IM server-side sync not configured, skipping profile_set")
            return False

        url = IMSyncService._build_url("profile", "portrait_set")

        profile_items = []
        # Nick: must be non-empty string, max 500 bytes
        if nickname and nickname.strip():
            if len(nickname.encode("utf-8")) <= 500:
                profile_items.append({"Tag": "Tag_Profile_IM_Nick", "Value": nickname})
            else:
                logger.warning(f"IM profile_set for {user_id}: nickname too long, skipping")
        # FaceUrl: must be non-empty full HTTP URL
        if avatar_url and avatar_url.strip():
            if avatar_url.startswith(("http://", "https://")):
                profile_items.append({"Tag": "Tag_Profile_IM_Image", "Value": avatar_url})
            else:
                logger.warning(
                    f"Skipping avatar update for {user_id}: "
                    f"not a full HTTP URL: {avatar_url[:80]}"
                )

        if not profile_items:
            logger.debug(f"No profile fields to update for {user_id}")
            return True

        payload = {
            "From_Account": user_id,
            "ProfileItem": profile_items,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                action_status = data.get("ActionStatus")
                error_code = data.get("ErrorCode")

                if action_status == "OK" and error_code == 0:
                    logger.info(f"IM profile updated for {user_id}")
                    return True
                elif error_code == 40003:
                    # Account doesn't exist in IM yet, import it first then retry
                    logger.info(f"IM account {user_id} not found, importing first")
                    await IMSyncService.import_account(user_id)
                    retry = await client.post(url, json=payload)
                    retry_data = retry.json()
                    if retry_data.get("ErrorCode") == 0:
                        logger.info(f"IM profile updated for {user_id} (after auto-import)")
                        return True
                    logger.warning(
                        f"IM profile_set retry failed for {user_id}: "
                        f"ErrorCode={retry_data.get('ErrorCode')}, ErrorInfo={retry_data.get('ErrorInfo')}"
                    )
                    return False
                else:
                    error_info = data.get("ErrorInfo", "")
                    logger.warning(
                        f"IM profile_set failed for {user_id}: "
                        f"ErrorCode={error_code}, ErrorInfo={error_info}"
                    )
                    return False

        except httpx.HTTPError as e:
            logger.error(f"IM profile_set HTTP error for {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"IM profile_set unexpected error for {user_id}: {e}")
            return False


# Convenience functions for direct import
async def sync_im_user_create(
    user_id: str,
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> bool:
    """Sync user creation to Tencent IM."""
    return await IMSyncService.import_account(user_id, nickname, avatar_url)


async def sync_im_user_delete(user_id: str) -> bool:
    """Sync user deletion to Tencent IM."""
    return await IMSyncService.delete_account(user_id)


async def sync_im_user_update(
    user_id: str,
    nickname: Optional[str] = None,
    avatar_url: Optional[str] = None,
) -> bool:
    """Sync user profile update to Tencent IM."""
    return await IMSyncService.set_profile(user_id, nickname, avatar_url)
