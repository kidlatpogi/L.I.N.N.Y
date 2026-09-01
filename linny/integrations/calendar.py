"""
Google Calendar integration with token caching and smart schedule summary.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, List, Optional, Tuple

import pytz
from dateutil import parser as date_parser

from ..core.config import USER_CONFIG_DIR, WORKSPACE_ROOT
from ..core.logger import get_logger

logger = get_logger("calendar")

TOKEN_FILE = USER_CONFIG_DIR / "token.json"
CREDENTIALS_FILE = WORKSPACE_ROOT / "credentials.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class CalendarClient:
    """Google Calendar Client for querying upcoming daily schedules."""

    def __init__(self, timezone_str: str = "Asia/Manila") -> None:
        self.timezone_str = timezone_str
        self.timezone = pytz.timezone(timezone_str)
        self.service = None
        self.school_cal_id: Optional[str] = None
        self._authenticated = False
        self._auth()

    def reload_timezone(self, timezone_str: str) -> None:
        self.timezone_str = timezone_str
        self.timezone = pytz.timezone(timezone_str)

    def _auth(self) -> None:
        """Authenticate with Google OAuth2."""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None
            if TOKEN_FILE.exists():
                try:
                    creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
                except Exception as e:
                    logger.warning(f"Failed to read token file: {e}")

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                    except Exception as e:
                        logger.warning(f"Failed to refresh token: {e}")
                        creds = None
                elif CREDENTIALS_FILE.exists():
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                        creds = flow.run_local_server(port=0)
                    except Exception as e:
                        logger.warning(f"OAuth flow error: {e}")

                if creds:
                    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                    with open(TOKEN_FILE, "w", encoding="utf-8") as f:
                        f.write(creds.to_json())

            if creds and creds.valid:
                self.service = build("calendar", "v3", credentials=creds)
                self._authenticated = True
                logger.info("Google Calendar successfully authenticated")
                self._find_school_calendar()
            else:
                logger.info("Google Calendar not configured (credentials.json missing)")
        except Exception as e:
            logger.warning(f"Calendar authentication unavailable: {e}")
            self.service = None
            self._authenticated = False

    def _find_school_calendar(self) -> None:
        """Locate secondary calendar named 'school' if available."""
        if not self.service:
            return
        try:
            cals = self.service.calendarList().list().execute()
            for cal in cals.get("items", []):
                if cal.get("summary", "").lower() == "school":
                    self.school_cal_id = cal["id"]
                    logger.info(f"Target calendar identified: {cal.get('summary')}")
                    return
        except Exception as e:
            logger.debug(f"Calendar list error: {e}")

    def _ensure_timezone(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            return self.timezone.localize(dt)
        return dt.astimezone(self.timezone)

    def get_schedule(self, query: str = "") -> str:
        """Fetch today's or tomorrow's events formatted for voice speech."""
        if not self.service or not self._authenticated:
            return "Calendar is not configured yet. Add your credentials.json to enable schedule tracking."

        try:
            now = datetime.now(self.timezone)
            q_lower = query.lower()
            is_tomorrow = any(w in q_lower for w in ["tomorrow", "bukas", "next day"])

            if is_tomorrow:
                target_day = now + timedelta(days=1)
                day_start = target_day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                label = "tomorrow"
            else:
                day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                label = "today"

            cal_id = self.school_cal_id or "primary"
            events_result = self.service.events().list(
                calendarId=cal_id,
                timeMin=day_start.isoformat(),
                timeMax=day_end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            ).execute()

            events = events_result.get("items", [])
            active_events: List[Tuple[Any, datetime, datetime]] = []

            for event in events:
                start_raw = event["start"].get("dateTime", event["start"].get("date"))
                end_raw = event["end"].get("dateTime", event["end"].get("date"))
                start_dt = self._ensure_timezone(date_parser.parse(start_raw))
                end_dt = self._ensure_timezone(date_parser.parse(end_raw))

                if label == "today" and end_dt < now:
                    continue  # Already finished
                active_events.append((event, start_dt, end_dt))

            # Smart switch to tomorrow if today is empty
            if not active_events and label == "today" and not is_tomorrow:
                logger.info("Today's schedule is clear, checking tomorrow...")
                return self.get_schedule("tomorrow")

            if not active_events:
                return f"You have no scheduled events for {label}."

            header = "Tomorrow's schedule" if label == "tomorrow" else "Today's schedule"
            summary_lines = [f"{header}: {len(active_events)} upcoming item{'s' if len(active_events) > 1 else ''}."]

            for event, start_dt, end_dt in active_events[:4]:
                name = event.get("summary", "Untitled event")
                if start_dt < now < end_dt:
                    summary_lines.append(f"{name} is ongoing until {end_dt.strftime('%I:%M %p')}.")
                else:
                    summary_lines.append(f"{name} from {start_dt.strftime('%I:%M %p')} to {end_dt.strftime('%I:%M %p')}.")

            return " ".join(summary_lines)

        except Exception as e:
            logger.error(f"Error reading calendar schedule: {e}")
            return "I couldn't retrieve your calendar schedule."

    def is_connected(self) -> bool:
        return self._authenticated
