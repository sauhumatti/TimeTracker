import os
import sqlite3
import datetime
from collections import defaultdict

class DatabaseManager:
    def __init__(self):
        self.db_filename = "timetracker.db"
        self.initialize_database()

    def initialize_database(self):
        """Create the database file and tables if they don't exist"""
        if not os.path.exists(self.db_filename):
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            # Create projects table
            cursor.execute('''
                CREATE TABLE projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TEXT,
                    last_active TEXT
                )
            ''')
            
            # Create activities table with project reference
            cursor.execute('''
                CREATE TABLE activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    type TEXT,
                    name TEXT,
                    window_title TEXT,
                    short_title TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            ''')
            
            # Create a default project
            cursor.execute('''
                INSERT INTO projects (name, description, created_at, last_active)
                VALUES (?, ?, ?, ?)
            ''', ("Default Project", "Default project for all activities", 
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()
        else:
            # Check if projects table exists, if not add it
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            # Check if projects table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
            if not cursor.fetchone():
                # Create projects table
                cursor.execute('''
                    CREATE TABLE projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        created_at TEXT,
                        last_active TEXT
                    )
                ''')
                
                # Add project_id column to activities if it doesn't exist
                cursor.execute("PRAGMA table_info(activities)")
                columns = [info[1] for info in cursor.fetchall()]
                
                if 'project_id' not in columns:
                    cursor.execute("ALTER TABLE activities ADD COLUMN project_id INTEGER")
                
                # Create a default project
                cursor.execute('''
                    INSERT INTO projects (name, description, created_at, last_active)
                    VALUES (?, ?, ?, ?)
                ''', ("Default Project", "Default project for all activities", 
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                
                conn.commit()
            
            conn.close()

    def initialize_database(self):
        """Create the database file and tables if they don't exist"""
        if not os.path.exists(self.db_filename):
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            # Create projects table
            cursor.execute('''
                CREATE TABLE projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at TEXT,
                    last_active TEXT
                )
            ''')
            
            # Create activities table with project reference
            cursor.execute('''
                CREATE TABLE activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    type TEXT,
                    name TEXT,
                    window_title TEXT,
                    short_title TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            ''')
            
            # Create a default project
            cursor.execute('''
                INSERT INTO projects (name, description, created_at, last_active)
                VALUES (?, ?, ?, ?)
            ''', ("Default Project", "Default project for all activities", 
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            conn.commit()
            conn.close()
        else:
            # Check if projects table exists, if not add it
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            # Check if projects table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
            if not cursor.fetchone():
                # Create projects table
                cursor.execute('''
                    CREATE TABLE projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        created_at TEXT,
                        last_active TEXT
                    )
                ''')
                
                # Add project_id column to activities if it doesn't exist
                cursor.execute("PRAGMA table_info(activities)")
                columns = [info[1] for info in cursor.fetchall()]
                
                if 'project_id' not in columns:
                    cursor.execute("ALTER TABLE activities ADD COLUMN project_id INTEGER")
                
                # Create a default project
                cursor.execute('''
                    INSERT INTO projects (name, description, created_at, last_active)
                    VALUES (?, ?, ?, ?)
                ''', ("Default Project", "Default project for all activities", 
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                
                conn.commit()
            
            conn.close()
            
    def get_today_activities_hierarchical(self, project_id=None):
        """Get today's activities as a hierarchy: app level with website children"""
        activities = self.get_today_activities(project_id)
        
        # First level: aggregate by application
        app_totals = defaultdict(lambda: {
            "name": "",
            "total_seconds": 0,
            "children": []
        })
        
        # Second level: group by website/window titles within each app
        website_totals = defaultdict(lambda: {
            "name": "",
            "window_title": "",
            "total_seconds": 0
        })
        
        # Process all activities
        for activity in activities:
            app_name = activity['name']
            window_title = activity['window_title']
            duration = activity['duration_seconds']
            
            # Add to application total
            if not app_totals[app_name]["name"]:
                app_totals[app_name]["name"] = app_name
            app_totals[app_name]["total_seconds"] += duration
            
            # Add to website total within this app
            key = f"{app_name}|{window_title}"
            if not website_totals[key]["name"]:
                website_totals[key]["name"] = app_name
                website_totals[key]["window_title"] = window_title
            website_totals[key]["total_seconds"] += duration
        
        # Build the hierarchy
        for key, website in website_totals.items():
            app_name = website["name"]
            app_totals[app_name]["children"].append({
                "window_title": website["window_title"],
                "total_seconds": website["total_seconds"],
                "duration_formatted": self._format_duration(datetime.timedelta(seconds=website["total_seconds"]))
            })
        
        # Format the app-level durations and sort children
        result = []
        for app_name, data in app_totals.items():
            # Format the duration
            data["duration_formatted"] = self._format_duration(datetime.timedelta(seconds=data["total_seconds"]))
            
            # Sort children by duration (most time first)
            data["children"].sort(key=lambda x: x["total_seconds"], reverse=True)
            
            # Add to result
            result.append(data)
        
        # Sort apps by duration (most time first)
        result.sort(key=lambda x: x["total_seconds"], reverse=True)
        
        return result

    def create_project(self, name, description=""):
        """Create a new project"""
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO projects (name, description, created_at, last_active)
                VALUES (?, ?, ?, ?)
            ''', (name, description, now, now))
            
            project_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            return project_id
        except sqlite3.IntegrityError:
            # Project with this name already exists
            return None
        except Exception as e:
            print(f"Error creating project: {e}")
            return None

    def get_projects(self):
        """Get all projects"""
        projects = []
        
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, name, description, created_at, last_active
                FROM projects
                ORDER BY last_active DESC
            ''')
            
            for row in cursor.fetchall():
                project = {
                    "id": row[0],
                    "name": row[1],
                    "description": row[2],
                    "created_at": row[3],
                    "last_active": row[4]
                }
                projects.append(project)
            
            conn.close()
        except Exception as e:
            print(f"Error retrieving projects: {e}")
        
        return projects

    def update_project(self, project_id, name, description):
        """Update a project"""
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE projects
                SET name = ?, description = ?
                WHERE id = ?
            ''', (name, description, project_id))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            print(f"Error updating project: {e}")
            return False

    def delete_project(self, project_id, transfer_to_default=True):
        """Delete a project"""
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            # Don't allow deleting the default project
            cursor.execute("SELECT id FROM projects WHERE name='Default Project'")
            default_id = cursor.fetchone()[0]
            
            if project_id == default_id:
                conn.close()
                return False, "Cannot delete the default project"
            
            # Handle activities associated with this project
            if transfer_to_default:
                # Transfer activities to default project
                cursor.execute('''
                    UPDATE activities 
                    SET project_id = ? 
                    WHERE project_id = ?
                ''', (default_id, project_id))
            else:
                # Delete activities associated with this project
                cursor.execute("DELETE FROM activities WHERE project_id = ?", (project_id,))
            
            # Delete the project
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            
            conn.commit()
            conn.close()
            
            return True, None
        except Exception as e:
            print(f"Error deleting project: {e}")
            return False, str(e)

    def update_project_last_active(self, project_id):
        """Update the last active timestamp of a project"""
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                UPDATE projects
                SET last_active = ?
                WHERE id = ?
            ''', (now, project_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating project last active: {e}")
    def save_activity(self, activity):
        """Save an activity to the database"""
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO activities (
                    project_id, type, name, window_title, short_title, start_time, end_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                activity.get("project_id", 1),  # Default to project ID 1 if not specified
                activity["type"],
                activity["name"],
                activity["window_title"],
                activity["short_title"],
                activity["start_time"].strftime("%Y-%m-%d %H:%M:%S"),
                activity["end_time"].strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            conn.commit()
            conn.close()
            
            # Update the last active timestamp of the project
            if "project_id" in activity:
                self.update_project_last_active(activity["project_id"])
                
        except Exception as e:
            print(f"Error saving activity: {e}")
    
    def get_today_activities(self, project_id=None):
        """Get all activities for the current day, optionally filtered by project"""
        activities = []
        
        try:
            conn = sqlite3.connect(self.db_filename)
            cursor = conn.cursor()
            
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            
            query = '''
                SELECT type, name, window_title, short_title, start_time, end_time
                FROM activities
                WHERE start_time LIKE ?
            '''
            params = [f"{today}%"]
            
            if project_id is not None:
                query += " AND project_id = ?"
                params.append(project_id)
                
            query += " ORDER BY start_time DESC"
            
            cursor.execute(query, params)
            
            rows = cursor.fetchall()
            
            for row in rows:
                start_time = datetime.datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S")
                end_time = datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")
                duration = end_time - start_time
                
                activity = {
                    "type": row[0],
                    "name": row[1],
                    "window_title": row[2],
                    "short_title": row[3],
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_formatted": self._format_duration(duration),
                    "duration_seconds": duration.total_seconds()
                }
                
                activities.append(activity)
            
            conn.close()
        except Exception as e:
            print(f"Error retrieving activities: {e}")
        
        return activities
        
    def get_today_activities_aggregated(self, project_id=None):
        """Get today's activities aggregated by application and window title"""
        activities = self.get_today_activities(project_id)
        
        # Use a dictionary to aggregate
        aggregated = defaultdict(lambda: {
            "name": "",
            "window_title": "",
            "short_title": "",
            "start_time": datetime.datetime.now(),
            "total_seconds": 0
        })
        
        for activity in activities:
            # For browsers, we want to track each tab separately
            if activity["name"].lower() in ['chrome', 'msedge', 'firefox', 'opera']:
                # We use both the app name and the full window title as the key
                key = (activity["name"], activity["window_title"])
            else:
                # For other apps, just use app name and window title
                key = (activity["name"], activity["window_title"])
            
            if key not in aggregated or activity["start_time"] < aggregated[key]["start_time"]:
                aggregated[key]["start_time"] = activity["start_time"]
                aggregated[key]["name"] = activity["name"]
                aggregated[key]["window_title"] = activity["window_title"]
            
            aggregated[key]["total_seconds"] += activity["duration_seconds"]
        
        # Convert to list and add formatted durations
        result = []
        for key, data in aggregated.items():
            # Convert seconds to timedelta for formatting
            duration = datetime.timedelta(seconds=int(data["total_seconds"]))
            
            result.append({
                "name": data["name"],
                "window_title": data["window_title"],
                "start_time": data["start_time"],
                "duration_formatted": self._format_duration(duration),
                "duration_seconds": data["total_seconds"]  # Keep this for sorting
            })
        
        # Sort by duration (descending)
        result.sort(key=lambda x: x["duration_seconds"], reverse=True)
        
        return result

    
    def _format_duration(self, duration):
        """Format a datetime.timedelta into a user-friendly string"""
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
        
        
