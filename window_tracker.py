import time
import datetime
from threading import Thread, Event
from PyQt5.QtCore import QObject, pyqtSignal
import win32gui
import win32process
import psutil

# Add to window_tracker.py

class WindowTracker(QObject):
    activity_changed = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.is_tracking = False
        self.stop_event = Event()
        self.tracking_thread = None
        self.current_activity = None
        self.current_project_id = 1  # Default project ID

        
    def start_tracking(self):
        if self.is_tracking:
            return
            
        self.is_tracking = True
        self.stop_event.clear()
        self.tracking_thread = Thread(target=self._track_windows)
        self.tracking_thread.daemon = True
        self.tracking_thread.start()
        
    def stop_tracking(self):
        if not self.is_tracking:
            return
            
        self.is_tracking = False
        self.stop_event.set()
        
        # Close the final activity if it exists
        if self.current_activity:
            self.current_activity["end_time"] = datetime.datetime.now()
            duration = self.current_activity["end_time"] - self.current_activity["start_time"]
            self.current_activity["duration_formatted"] = self._format_duration(duration)
            self.activity_changed.emit(self.current_activity)
            self.current_activity = None
        
        if self.tracking_thread:
            self.tracking_thread.join(timeout=1.0)
            
    def _track_windows(self):
        last_window_title = None
        last_app_name = None
        last_domain_info = None
        
        try:
            while not self.stop_event.is_set():
                current_window_handle = win32gui.GetForegroundWindow()
                app_name, window_title, domain_info = self._get_window_info(current_window_handle)
                
                # Skip empty window titles (typically system windows)
                if not window_title.strip():
                    time.sleep(1)
                    continue
                
                # Key change: Check for both app and full title to detect tab changes
                current_identifier = f"{app_name}::{window_title}"
                last_identifier = f"{last_app_name}::{last_window_title}" if last_window_title else None
                
                # If the window/tab has changed
                if current_identifier != last_identifier:
                    # Close previous activity if there is one
                    if self.current_activity:
                        self.current_activity["end_time"] = datetime.datetime.now()
                        duration = self.current_activity["end_time"] - self.current_activity["start_time"]
                        self.current_activity["duration_formatted"] = self._format_duration(duration)
                        self.activity_changed.emit(self.current_activity)
                    
                    # Create a new activity
                    short_title = window_title[:27] + "..." if len(window_title) > 30 else window_title
                    
                    self.current_activity = {
                        "type": "Application",
                        "name": app_name,
                        "window_title": window_title,
                        "short_title": short_title,
                        "domain_info": domain_info,  # Add domain info for grouping
                        "start_time": datetime.datetime.now(),
                        "end_time": datetime.datetime.now(),  # Will be updated when window changes
                        "duration_formatted": "0s"
                    }
                    
                    last_window_title = window_title
                    last_app_name = app_name
                    last_domain_info = domain_info
                elif self.current_activity:
                    # Update end time for current activity
                    self.current_activity["end_time"] = datetime.datetime.now()
                
                # Check every second
                time.sleep(1)
                
        except Exception as e:
            print(f"Error in window tracking: {e}")
    
    def _get_window_info(self, hwnd):
        window_title = win32gui.GetWindowText(hwnd)
        
        app_name = "Unknown"
        domain_info = "Other"
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            if pid > 0:
                process = psutil.Process(pid)
                app_name = process.name().replace('.exe', '')
                
                # Clean browser titles and get domain info for better grouping
                if app_name.lower() in ['chrome', 'msedge', 'firefox', 'opera']:
                    cleaned_title, domain_info = self._clean_browser_title(app_name, window_title)
                    window_title = cleaned_title
                
        except Exception as e:
            print(f"Error getting process info: {e}")
        
        return app_name, window_title, domain_info

    def _clean_browser_title(self, app_name, window_title):
        """Clean and standardize browser tab titles"""
        # Map of browser process names to their window title suffixes
        browser_suffixes = {
            'chrome': ['- Google Chrome', '- Chrome'],
            'msedge': ['- Microsoft Edge', '- Edge'],
            'firefox': ['- Mozilla Firefox', '- Firefox'],
            'opera': ['- Opera']
        }
        
        # Check if this is a known browser
        app_lower = app_name.lower()
        cleaned_title = window_title
        
        for browser, suffixes in browser_suffixes.items():
            if app_lower == browser:
                # Remove the browser name suffix from the title
                for suffix in suffixes:
                    if window_title.endswith(suffix):
                        cleaned_title = window_title[:-len(suffix)].strip()
        
        # Extract the domain info and original title
        domain_info = self._extract_domain_info(cleaned_title)
        
        return cleaned_title, domain_info
    
    def _extract_domain_info(self, window_title):
        """Extract domain information from window title for grouping similar sites"""
        # Common sites and their identifiers
        site_patterns = {
            'Reddit': [' : r/', 'r/'],
            'YouTube': ['- YouTube', 'YouTube'],
            'LinkedIn': ['| LinkedIn', 'LinkedIn'],
            'Twitter': ['/ X', '| X', 'Twitter'],
            'Facebook': ['| Facebook', 'Facebook'],
            'GitHub': ['GitHub'],
            'Google': ['Google'],
            'Gmail': ['Gmail'],
            'Amazon': ['Amazon'],
            'Stack Overflow': ['Stack Overflow'],
            'Medium': ['Medium'],
            'Wikipedia': ['Wikipedia'],
            'Netflix': ['Netflix'],
            'Twitch': ['Twitch']
        }
        
        # Check for each site pattern
        for site_name, patterns in site_patterns.items():
            for pattern in patterns:
                if pattern in window_title:
                    return site_name
        
        # If no match found, default to "Other"
        return "Other"

    def _format_duration(self, duration):
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
