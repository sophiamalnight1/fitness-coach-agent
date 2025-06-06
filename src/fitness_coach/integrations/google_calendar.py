import os
import json
import streamlit as st
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz  # Add this import for timezone handling


class GoogleCalendarService:
    """Fixed Google Calendar integration with proper timezone handling."""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    
    def __init__(self):
        """Initialize the Google Calendar service."""
        self.service = None
        self.credentials = None
        # Set default timezone - you can make this configurable
        self.timezone = pytz.timezone('America/New_York')  # Make this configurable
        
        # Try to initialize service if credentials exist
        if 'google_credentials' in st.session_state:
            try:
                self._initialize_service()
            except Exception as e:
                print(f"DEBUG: Failed to initialize service in __init__: {e}")
    
    def _make_timezone_aware(self, dt: datetime) -> datetime:
        """Convert naive datetime to timezone-aware datetime."""
        if dt.tzinfo is None:
            return self.timezone.localize(dt)
        return dt
    
    def _make_timezone_naive(self, dt: datetime) -> datetime:
        """Convert timezone-aware datetime to naive datetime in local timezone."""
        if dt.tzinfo is not None:
            return dt.astimezone(self.timezone).replace(tzinfo=None)
        return dt

    def get_busy_times(self, start_date: datetime, end_date: datetime, 
                      calendar_ids: List[str] = None) -> List[Dict]:
        """Get busy times from calendar(s) with fixed timezone handling."""
        if not self.service:
            self._initialize_service()
        
        if not calendar_ids:
            # Use primary calendar
            calendars = self.get_calendars()
            calendar_ids = [cal['id'] for cal in calendars if cal['primary']]
        
        try:
            # FIXED: Ensure start_date and end_date are timezone-aware
            start_aware = self._make_timezone_aware(start_date)
            end_aware = self._make_timezone_aware(end_date)
            
            freebusy_query = {
                'timeMin': start_aware.isoformat(),
                'timeMax': end_aware.isoformat(),
                'items': [{'id': cal_id} for cal_id in calendar_ids]
            }
            
            freebusy_result = self.service.freebusy().query(body=freebusy_query).execute()
            
            busy_times = []
            for cal_id in calendar_ids:
                if cal_id in freebusy_result['calendars']:
                    for busy_period in freebusy_result['calendars'][cal_id]['busy']:
                        # FIXED: Parse ISO format properly and convert to naive datetime
                        start_str = busy_period['start']
                        end_str = busy_period['end']
                        
                        # Parse ISO datetime strings
                        busy_start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                        busy_end = datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                        
                        # Convert to local timezone and make naive
                        busy_start_naive = self._make_timezone_naive(busy_start)
                        busy_end_naive = self._make_timezone_naive(busy_end)
                        
                        busy_times.append({
                            'start': busy_start_naive,
                            'end': busy_end_naive,
                            'calendar_id': cal_id
                        })
            
            return busy_times
            
        except HttpError as e:
            print(f"Error fetching busy times: {e}")
            return []

    def find_available_slots(self, start_date: datetime, end_date: datetime,
                           duration_minutes: int, work_hours: Dict = None,
                           preferences: Dict = None) -> List[Dict]:
        """Find available time slots for workouts with fixed timezone handling."""
        # FIXED: Ensure all datetime objects are naive for consistent comparison
        start_naive = self._make_timezone_naive(start_date) if start_date.tzinfo else start_date
        end_naive = self._make_timezone_naive(end_date) if end_date.tzinfo else end_date
        
        # Get busy times (these will be returned as naive datetimes)
        busy_times = self.get_busy_times(start_naive, end_naive)
        
        # Default work hours if not provided
        if not work_hours:
            work_hours = {
                'start_time': time(9, 0),  # 9 AM
                'end_time': time(17, 0),   # 5 PM
                'work_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'allow_lunch_workouts': True,
                'lunch_start': time(12, 0),
                'lunch_end': time(13, 0)
            }
        
        available_slots = []
        current_date = start_naive.date()
        
        while current_date <= end_naive.date():
            day_name = current_date.strftime('%A')
            
            # Define potential workout windows
            workout_windows = self._get_workout_windows(current_date, work_hours, day_name)
            
            # Check each window for availability
            for window_start, window_end, window_type in workout_windows:
                # FIXED: Ensure window times are naive
                window_start_naive = self._make_timezone_naive(window_start) if window_start.tzinfo else window_start
                window_end_naive = self._make_timezone_naive(window_end) if window_end.tzinfo else window_end
                
                available_slots.extend(
                    self._find_slots_in_window(
                        window_start_naive, window_end_naive, duration_minutes, 
                        busy_times, window_type, preferences
                    )
                )
            
            current_date += timedelta(days=1)
        
        return available_slots
    
    def _get_workout_windows(self, date: datetime.date, work_hours: Dict, day_name: str) -> List[Tuple]:
        """Get potential workout time windows for a day - returns naive datetimes."""
        windows = []
        
        # Create naive datetime objects
        work_start = datetime.combine(date, work_hours['start_time'])
        work_end = datetime.combine(date, work_hours['end_time'])
        
        # Early morning (6 AM - work start)
        early_start = datetime.combine(date, time(6, 0))
        if early_start < work_start:
            windows.append((early_start, work_start, 'early_morning'))
        
        # Lunch break (if allowed and it's a work day)
        if (work_hours.get('allow_lunch_workouts', False) and 
            day_name in work_hours.get('work_days', [])):
            lunch_start = datetime.combine(date, work_hours.get('lunch_start', time(12, 0)))
            lunch_end = datetime.combine(date, work_hours.get('lunch_end', time(13, 0)))
            windows.append((lunch_start, lunch_end, 'lunch'))
        
        # Evening (work end - 10 PM)
        evening_end = datetime.combine(date, time(22, 0))
        if work_end < evening_end:
            # If weekend, start earlier
            if day_name not in work_hours.get('work_days', []):
                afternoon_start = datetime.combine(date, time(14, 0))
                windows.append((afternoon_start, evening_end, 'afternoon'))
            else:
                windows.append((work_end, evening_end, 'evening'))
        
        return windows
    
    def _find_slots_in_window(self, window_start: datetime, window_end: datetime,
                            duration_minutes: int, busy_times: List[Dict],
                            window_type: str, preferences: Dict = None) -> List[Dict]:
        """Find available slots within a specific time window - all naive datetimes."""
        slots = []
        slot_duration = timedelta(minutes=duration_minutes)
        
        # FIXED: All datetime objects are now naive, so comparison should work
        # Filter busy times that overlap with this window
        relevant_busy = [
            busy for busy in busy_times
            if not (busy['end'] <= window_start or busy['start'] >= window_end)
        ]
        
        # Sort by start time
        relevant_busy.sort(key=lambda x: x['start'])
        
        current_time = window_start
        
        # Check for slots before first busy period
        if relevant_busy and relevant_busy[0]['start'] > current_time:
            potential_end = min(relevant_busy[0]['start'], window_end)
            if potential_end - current_time >= slot_duration:
                slots.append({
                    'start': current_time,
                    'end': current_time + slot_duration,
                    'window_type': window_type,
                    'available_duration': int((potential_end - current_time).total_seconds() / 60)
                })
        
        # Check for slots between busy periods
        for i in range(len(relevant_busy) - 1):
            gap_start = relevant_busy[i]['end']
            gap_end = relevant_busy[i + 1]['start']
            
            if gap_start < gap_end and gap_end - gap_start >= slot_duration:
                slots.append({
                    'start': gap_start,
                    'end': gap_start + slot_duration,
                    'window_type': window_type,
                    'available_duration': int((gap_end - gap_start).total_seconds() / 60)
                })
        
        # Check for slots after last busy period
        if relevant_busy:
            last_busy_end = relevant_busy[-1]['end']
            if last_busy_end < window_end and window_end - last_busy_end >= slot_duration:
                slots.append({
                    'start': last_busy_end,
                    'end': last_busy_end + slot_duration,
                    'window_type': window_type,
                    'available_duration': int((window_end - last_busy_end).total_seconds() / 60)
                })
        elif window_end - window_start >= slot_duration:
            # No busy periods in this window
            slots.append({
                'start': window_start,
                'end': window_start + slot_duration,
                'window_type': window_type,
                'available_duration': int((window_end - window_start).total_seconds() / 60)
            })
        
        return slots
    
    def create_workout_event(self, workout_details: Dict, start_time: datetime,
                           duration_minutes: int, calendar_id: str = 'primary') -> str:
        """Create a workout event in Google Calendar with proper timezone handling."""
        if not self.service:
            self._initialize_service()
        
        # FIXED: Ensure start_time is timezone-aware for Google Calendar API
        start_aware = self._make_timezone_aware(start_time)
        end_aware = start_aware + timedelta(minutes=duration_minutes)
        
        event = {
            'summary': f"🏋️‍♂️ {workout_details.get('type', 'Workout')} - {workout_details.get('focus', '')}",
            'description': self._format_workout_description(workout_details),
            'start': {
                'dateTime': start_aware.isoformat(),
                'timeZone': str(self.timezone),
            },
            'end': {
                'dateTime': end_aware.isoformat(),
                'timeZone': str(self.timezone),
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 15},
                    {'method': 'popup', 'minutes': 5},
                ],
            },
            'colorId': '4',  # Green color for workouts
        }
        
        # Add location if specified
        location = workout_details.get('location', '')
        if location and location != 'N/A':
            event['location'] = location
        
        try:
            created_event = self.service.events().insert(
                calendarId=calendar_id, body=event
            ).execute()
            
            return created_event['id']
            
        except HttpError as e:
            print(f"Error creating event: {e}")
            return None

    # ... (rest of the methods remain the same)
    def is_authenticated(self) -> bool:
        """Check if user is authenticated with Google Calendar - FIXED."""
        try:
            # First check if we have credentials in session state
            if 'google_credentials' not in st.session_state:
                print("DEBUG: No google_credentials in session state")
                return False
            
            # Clean the credentials data before creating the object
            creds_data = self._clean_credentials_data(st.session_state.google_credentials)
            
            # Try to create credentials object
            creds = Credentials.from_authorized_user_info(creds_data, self.SCOPES)
            
            print(f"DEBUG: Credentials object created - valid: {creds.valid}, expired: {creds.expired}")
            
            # If credentials are expired but we have a refresh token, try to refresh
            if creds.expired and creds.refresh_token:
                print("DEBUG: Credentials expired, attempting refresh in is_authenticated")
                try:
                    creds.refresh(Request())
                    print("DEBUG: Credentials refreshed successfully in is_authenticated")
                    
                    # Update stored credentials with proper serialization
                    self._update_stored_credentials(creds)
                    
                    # Update our instance credentials
                    self.credentials = creds
                    
                    print(f"DEBUG: Updated credentials - valid: {creds.valid}")
                    
                except Exception as refresh_error:
                    print(f"DEBUG: Failed to refresh credentials: {refresh_error}")
                    return False
            
            # Check if credentials are valid
            if creds and creds.valid:
                # Ensure service is initialized
                if not self.service:
                    try:
                        self.service = build('calendar', 'v3', credentials=creds)
                        self.credentials = creds
                        print("DEBUG: Service initialized in is_authenticated")
                    except Exception as service_error:
                        print(f"DEBUG: Failed to initialize service: {service_error}")
                        return False
                
                print("DEBUG: Authentication check passed")
                return True
            else:
                print(f"DEBUG: Credentials not valid - valid: {creds.valid if creds else 'None'}")
                return False
                
        except Exception as e:
            print(f"DEBUG: Auth check error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _clean_credentials_data(self, creds_data: dict) -> dict:
        """Clean credentials data to ensure proper format for Google API."""
        cleaned_data = creds_data.copy()
        
        # Handle expiry field - must be string or None
        if 'expiry' in cleaned_data:
            expiry = cleaned_data['expiry']
            if expiry is None:
                # Remove None expiry
                cleaned_data.pop('expiry', None)
            elif isinstance(expiry, datetime):
                # Convert datetime to ISO string
                cleaned_data['expiry'] = expiry.isoformat()
            elif isinstance(expiry, str):
                # Already a string, keep as is
                pass
            else:
                # Unknown type, remove it
                print(f"DEBUG: Unexpected expiry type: {type(expiry)}, removing")
                cleaned_data.pop('expiry', None)
        
        print(f"DEBUG: Cleaned credentials data - expiry type: {type(cleaned_data.get('expiry', 'None'))}")
        return cleaned_data
    
    def _update_stored_credentials(self, creds: Credentials):
        """Update stored credentials with proper serialization."""
        st.session_state.google_credentials.update({
            'token': creds.token,
            'refresh_token': creds.refresh_token,
            'expiry': creds.expiry.isoformat() if creds.expiry else None
        })
        print("DEBUG: Stored credentials updated with proper serialization")
    
    def get_auth_url(self) -> str:
        """Get Google OAuth authorization URL with better error handling."""
        try:
            client_id = os.getenv("GOOGLE_CLIENT_ID")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
            
            print(f"DEBUG: Client ID exists: {bool(client_id)}")
            print(f"DEBUG: Client Secret exists: {bool(client_secret)}")
            
            if not client_id or not client_secret:
                raise ValueError("Google Calendar credentials not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your .env file.")
            
            client_config = {
                "web": {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8501"]
                }
            }
            
            flow = Flow.from_client_config(
                client_config,
                scopes=self.SCOPES,
                redirect_uri="http://localhost:8501"
            )
            
            # Store flow in session state for later use
            st.session_state.auth_flow = flow
            
            auth_url, state = flow.authorization_url(
                prompt='consent',
                access_type='offline',  # This ensures we get a refresh token
                include_granted_scopes='true'
            )
            
            print(f"DEBUG: Generated auth URL: {auth_url[:100]}...")
            return auth_url
            
        except Exception as e:
            print(f"DEBUG: Error generating auth URL: {e}")
            raise
    
    def authenticate_with_code(self, auth_code: str) -> bool:
        """Authenticate using authorization code with improved persistence."""
        try:
            print(f"DEBUG: Starting authentication with code: {auth_code[:20]}...")
            
            # Get the flow from session state
            if 'auth_flow' not in st.session_state:
                print("DEBUG: No auth_flow in session state")
                st.error("Authentication flow not found. Please start over.")
                return False
            
            flow = st.session_state.auth_flow
            print("DEBUG: Retrieved flow from session state")
            
            # Exchange the authorization code for credentials
            print("DEBUG: Fetching token...")
            flow.fetch_token(code=auth_code)
            print("DEBUG: Token fetched successfully")
            
            # Store credentials in session state with proper serialization
            credentials_data = {
                'token': flow.credentials.token,
                'refresh_token': flow.credentials.refresh_token,
                'token_uri': flow.credentials.token_uri,
                'client_id': flow.credentials.client_id,
                'client_secret': flow.credentials.client_secret,
                'scopes': flow.credentials.scopes,
                # FIXED: Always convert expiry to string format
                'expiry': flow.credentials.expiry.isoformat() if flow.credentials.expiry else None
            }
            
            print(f"DEBUG: Storing credentials - token exists: {bool(credentials_data['token'])}")
            print(f"DEBUG: Refresh token exists: {bool(credentials_data['refresh_token'])}")
            print(f"DEBUG: Expiry: {credentials_data['expiry']} (type: {type(credentials_data['expiry'])})")
            
            st.session_state.google_credentials = credentials_data
            
            # Store credentials in instance
            self.credentials = flow.credentials
            
            # Clean up the flow
            del st.session_state.auth_flow
            print("DEBUG: Cleaned up auth flow")
            
            # Initialize service immediately
            print("DEBUG: Initializing service immediately after authentication...")
            self._initialize_service()
            
            # Test authentication immediately
            auth_test = self.is_authenticated()
            print(f"DEBUG: Immediate auth test result: {auth_test}")
            
            if not auth_test:
                print("DEBUG: WARNING - Authentication test failed immediately after setup")
                # Try one more time to initialize
                self._initialize_service()
                auth_test = self.is_authenticated()
                print(f"DEBUG: Second auth test result: {auth_test}")
            
            return auth_test
            
        except Exception as e:
            print(f"DEBUG: Authentication error: {str(e)}")
            import traceback
            traceback.print_exc()
            st.error(f"Authentication error: {str(e)}")
            return False
    
    def authenticate_with_url(self, callback_url: str) -> bool:
        """Authenticate using the full callback URL with better error handling."""
        try:
            print(f"DEBUG: Starting URL authentication with: {callback_url[:100]}...")
            
            # Extract the authorization code from the URL
            if "code=" not in callback_url:
                print("DEBUG: No 'code=' found in URL")
                st.error("No authorization code found in URL. Make sure you copied the complete redirect URL.")
                return False
            
            # Parse the code from the URL
            import urllib.parse as urlparse
            print("DEBUG: Parsing URL...")
            
            parsed_url = urlparse.urlparse(callback_url)
            print(f"DEBUG: Parsed URL query: {parsed_url.query}")
            
            query_params = urlparse.parse_qs(parsed_url.query)
            print(f"DEBUG: Query params: {list(query_params.keys())}")
            
            auth_code = query_params.get('code', [None])[0]
            
            if not auth_code:
                print("DEBUG: Could not extract code from query params")
                st.error("Could not extract authorization code from URL. Please check the URL format.")
                return False
            
            print(f"DEBUG: Extracted code: {auth_code[:20]}...")
            
            return self.authenticate_with_code(auth_code)
            
        except Exception as e:
            print(f"DEBUG: URL authentication error: {str(e)}")
            import traceback
            traceback.print_exc()
            st.error(f"URL authentication error: {str(e)}")
            return False
    
    def _initialize_service(self):
        """Initialize the Google Calendar service with improved error handling."""
        if 'google_credentials' not in st.session_state:
            print("DEBUG: No credentials in session state for service initialization")
            return
            
        try:
            print("DEBUG: Initializing service from stored credentials")
            
            # Clean the credentials data before using it
            creds_data = self._clean_credentials_data(st.session_state.google_credentials)
            
            print(f"DEBUG: Using credentials with expiry type: {type(creds_data.get('expiry', 'None'))}")
            
            # Create credentials object
            creds = Credentials.from_authorized_user_info(creds_data, self.SCOPES)
            
            print(f"DEBUG: Credentials created - valid: {creds.valid}")
            print(f"DEBUG: Credentials expired: {creds.expired}")
            print(f"DEBUG: Has refresh token: {bool(creds.refresh_token)}")
            
            # If expired, refresh immediately
            if creds.expired and creds.refresh_token:
                print("DEBUG: Refreshing expired credentials during initialization")
                creds.refresh(Request())
                
                # Update stored credentials with proper serialization
                self._update_stored_credentials(creds)
                print("DEBUG: Credentials refreshed and updated in session state")
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=creds)
            self.credentials = creds
            
            print("DEBUG: Service successfully initialized")
            
            # Test the service immediately
            try:
                test_result = self.service.calendarList().list(maxResults=1).execute()
                print(f"DEBUG: Service test successful - found {len(test_result.get('items', []))} calendars")
            except Exception as test_error:
                print(f"DEBUG: Service test failed: {test_error}")
                # Don't raise here, might be a temporary issue
                
        except Exception as e:
            print(f"DEBUG: Service initialization error: {str(e)}")
            import traceback
            traceback.print_exc()
            # Clear invalid credentials
            if 'google_credentials' in st.session_state:
                print("DEBUG: Clearing invalid credentials from session state")
                del st.session_state.google_credentials
            raise
    
    def get_calendars(self) -> List[Dict]:
        """Get list of user's calendars."""
        if not self.service:
            self._initialize_service()
        
        try:
            calendars_result = self.service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            return [{
                'id': cal['id'],
                'name': cal['summary'],
                'primary': cal.get('primary', False)
            } for cal in calendars]
            
        except HttpError as e:
            print(f"Error fetching calendars: {e}")
            return []
    
    def _format_workout_description(self, workout_details: Dict) -> str:
        """Format workout details for calendar event description."""
        description_parts = []
        
        description_parts.append(f"💪 Intensity: {workout_details.get('intensity', 'Moderate')}")
        description_parts.append(f"🎯 Focus: {workout_details.get('focus', 'General fitness')}")
        
        if workout_details.get('details') and workout_details['details'] != 'N/A':
            description_parts.append(f"\n📝 Workout Details:\n{workout_details['details']}")
        
        description_parts.append(f"\n⏱️ Duration: {workout_details.get('duration', 'N/A')}")
        
        description_parts.append("\n🤖 Generated by AI Fitness Coach")
        
        return '\n'.join(description_parts)