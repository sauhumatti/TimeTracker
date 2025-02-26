from PyQt5.QtWidgets import (QMainWindow, QTreeWidget, QTreeWidgetItem, QPushButton, 
                             QLabel, QVBoxLayout, QHBoxLayout, QWidget, QTableWidgetItem,
                             QSystemTrayIcon, QMenu, QAction, QDialog, QLineEdit,
                             QTextEdit, QComboBox, QMessageBox, QInputDialog, QApplication)

from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal

from database_manager import DatabaseManager
from window_tracker import WindowTracker

import datetime
from collections import defaultdict
import sys
import os

class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.db_manager = DatabaseManager()
        self.window_tracker = WindowTracker()
        self.window_tracker.activity_changed.connect(self.on_activity_changed)
        
        self.is_tracking = False
        self.current_project_id = 1  # Default project ID
        self.projects = self.db_manager.get_projects()
        
        self.init_ui()
        self.setup_system_tray()
        
        # Set up timer to refresh data periodically
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.update_activity_display)
        self.refresh_timer.start(60000)  # Refresh every minute
        
        self.update_activity_display()
    
    def init_ui(self):
        """Initialize the UI components"""
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Create project selection area
        project_layout = QHBoxLayout()
        
        # Project label and combo box
        project_layout.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        project_layout.addWidget(self.project_combo)
        
        # Project management buttons
        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.clicked.connect(self.create_project_dialog)
        project_layout.addWidget(self.new_project_btn)
        
        self.edit_project_btn = QPushButton("Edit")
        self.edit_project_btn.clicked.connect(self.edit_project_dialog)
        project_layout.addWidget(self.edit_project_btn)
        
        self.delete_project_btn = QPushButton("Delete")
        self.delete_project_btn.clicked.connect(self.delete_project_dialog)
        project_layout.addWidget(self.delete_project_btn)
        
        main_layout.addLayout(project_layout)
        
        # Create tracking control area
        tracking_layout = QHBoxLayout()
        
        self.tracking_btn = QPushButton("Start Tracking")
        self.tracking_btn.clicked.connect(self.toggle_tracking)
        tracking_layout.addWidget(self.tracking_btn)
        
        self.tracking_status = QLabel("Tracking stopped")
        tracking_layout.addWidget(self.tracking_status)
        tracking_layout.addStretch()
        
        main_layout.addLayout(tracking_layout)
        
        # Create activity tree widget
        self.activity_table = QTreeWidget()
        self.activity_table.setColumnCount(2)
        self.activity_table.setHeaderLabels(["Application", "Duration"])
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.header().setStretchLastSection(True)
        self.activity_table.setColumnWidth(0, 300)
        self.activity_table.itemClicked.connect(self.on_item_clicked)
        
        main_layout.addWidget(self.activity_table)
        
        # Set the main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # Set window properties
        self.setWindowTitle("Python Time Tracker")
        self.setGeometry(100, 100, 800, 600)
    
    def update_project_combo(self):
        """Update the project selection dropdown"""
        self.project_combo.clear()
        self.projects = self.db_manager.get_projects()
        
        selected_index = 0
        for i, project in enumerate(self.projects):
            self.project_combo.addItem(project["name"], project["id"])
            if project["id"] == self.current_project_id:
                selected_index = i
        
        self.project_combo.setCurrentIndex(selected_index)
    
    def on_project_changed(self, index):
        """Handle project selection change"""
        if index >= 0 and index < len(self.projects):
            self.current_project_id = self.projects[index]["id"]
            self.update_activity_display()
    
    def create_project_dialog(self):
        """Show dialog to create a new project"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Create New Project")
        dialog.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        name_label = QLabel("Project Name:")
        layout.addWidget(name_label)
        
        name_input = QLineEdit()
        layout.addWidget(name_input)
        
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)
        
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(80)
        layout.addWidget(desc_input)
        
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        create_btn = QPushButton("Create")
        create_btn.clicked.connect(lambda: self.finish_create_project(name_input.text(), desc_input.toPlainText(), dialog))
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        dialog.exec_()
    
    def finish_create_project(self, name, description, dialog):
        """Create a new project with the given details"""
        if not name.strip():
            QMessageBox.warning(self, "Validation Error", "Project name cannot be empty.")
            return
            
        project_id = self.db_manager.create_project(name, description)
        
        if project_id is None:
            QMessageBox.warning(self, "Error", "A project with this name already exists.")
            return
            
        dialog.accept()
        self.current_project_id = project_id
        self.update_project_combo()
        self.update_activity_display()
    
    def edit_project_dialog(self):
        """Show dialog to edit the current project"""
        current_project = None
        for project in self.projects:
            if project["id"] == self.current_project_id:
                current_project = project
                break
                
        if not current_project:
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Edit Project: {current_project['name']}")
        dialog.setFixedWidth(400)
        
        layout = QVBoxLayout()
        
        name_label = QLabel("Project Name:")
        layout.addWidget(name_label)
        
        name_input = QLineEdit(current_project["name"])
        layout.addWidget(name_input)
        
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)
        
        desc_input = QTextEdit()
        desc_input.setPlainText(current_project["description"] or "")
        desc_input.setMaximumHeight(80)
        layout.addWidget(desc_input)
        
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self.update_project(
            self.current_project_id, name_input.text(), desc_input.toPlainText(), dialog))
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        
        dialog.exec_()
    
    def update_project(self, project_id, name, description, dialog):
        """Update the project with the given details"""
        if not name.strip():
            QMessageBox.warning(self, "Validation Error", "Project name cannot be empty.")
            return
            
        success = self.db_manager.update_project(project_id, name, description)
        
        if not success:
            QMessageBox.warning(self, "Error", "Failed to update project. The name may already be in use.")
            return
            
        dialog.accept()
        self.update_project_combo()
    
    def delete_project_dialog(self):
        """Show confirmation dialog to delete the current project"""
        current_project = None
        for project in self.projects:
            if project["id"] == self.current_project_id:
                current_project = project
                break
                
        if not current_project:
            return
            
        reply = QMessageBox.question(
            self, 
            "Confirm Delete",
            f"Are you sure you want to delete project '{current_project['name']}'?\n\n"
            "You can either transfer its activities to the default project or delete them.",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Yes:
            # Transfer activities
            success, error = self.db_manager.delete_project(self.current_project_id, True)
            if not success:
                QMessageBox.warning(self, "Error", error or "Failed to delete project.")
            self.current_project_id = 1  # Reset to default project
            self.update_project_combo()
            self.update_activity_display()
        elif reply == QMessageBox.No:
            # Delete activities
            confirm = QMessageBox.question(
                self,
                "Confirm Delete Activities",
                "This will delete all activities in this project. Are you sure?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                success, error = self.db_manager.delete_project(self.current_project_id, False)
                if not success:
                    QMessageBox.warning(self, "Error", error or "Failed to delete project.")
                self.current_project_id = 1  # Reset to default project
                self.update_project_combo()
                self.update_activity_display()
    
    def toggle_tracking(self):
        """Start or stop activity tracking"""
        self.is_tracking = not self.is_tracking
        
        if self.is_tracking:
            self.tracking_status.setText("Initializing tracker...")
            # Set the current project for tracking
            self.window_tracker.current_project_id = self.current_project_id
            self.window_tracker.start_tracking()
            self.tracking_btn.setText("Stop Tracking")
            self.tracking_status.setText("Tracking active...")
        else:
            self.window_tracker.stop_tracking()
            self.tracking_btn.setText("Start Tracking")
            self.tracking_status.setText("Tracking stopped")
    
    def on_activity_changed(self, activity):
        """Handle activity change event from tracker"""
        # Add project_id to activity before saving
        activity["project_id"] = self.current_project_id
        # Save the activity to the database
        self.db_manager.save_activity(activity)
        
        # Update status and refresh view
        self.tracking_status.setText(f"Tracking: {activity['name']} - {activity['short_title']}")
        self.update_activity_display()
    
    def update_activity_display(self):
        """Update the activity display with hierarchical data"""
        self.activity_table.clear()
        
        if not self.db_manager:
            return
        
        # Get hierarchical activity data
        activities = self.db_manager.get_today_activities_hierarchical(self.current_project_id)
        
        for app_data in activities:
            # Create app-level item
            app_item = QTreeWidgetItem(self.activity_table)
            app_item.setText(0, app_data["name"])
            app_item.setText(1, app_data["duration_formatted"])
            app_item.setData(0, Qt.UserRole, "app")  # Tag as an app item
            
            # For chrome, we'll expand to show websites
            if app_data["name"].lower() == "chrome":
                for website in app_data["children"]:
                    # Create website-level item
                    site_item = QTreeWidgetItem(app_item)
                    site_item.setText(0, website["window_title"])
                    site_item.setText(1, website["duration_formatted"])
                    site_item.setData(0, Qt.UserRole, "website")  # Tag as a website item
        
        # Set column widths
        self.activity_table.setColumnWidth(0, 300)

    def on_item_clicked(self, item, column):
        """Handle clicks on tree items to expand/collapse"""
        item_type = item.data(0, Qt.UserRole)
        
        # Only handle app-level items
        if item_type == "app":
            # Toggle expansion
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
    
    def setup_system_tray(self):
        """Set up system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Try to set an icon - you'll need to add an icon file to your project
        try:
            self.tray_icon.setIcon(QIcon("icon.png"))  # Replace with your icon path
        except:
            print("Could not load tray icon")
        
        # Create the tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        hide_action = QAction("Hide", self)
        hide_action.triggered.connect(self.hide)
        tray_menu.addAction(hide_action)
        
        toggle_action = QAction("Start Tracking" if not self.is_tracking else "Stop Tracking", self)
        toggle_action.triggered.connect(self.toggle_tracking)
        tray_menu.addAction(toggle_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close_application)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Connect tray icon activation
        self.tray_icon.activated.connect(self.tray_icon_activated)

    def tray_icon_activated(self, reason):
        """Handle system tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def close_application(self):
        """Properly close the application"""
        if self.is_tracking:
            self.toggle_tracking()  # Stop tracking
        self.close()
        QApplication.quit()

    def closeEvent(self, event):
        """Handle window close event"""
        if self.tray_icon.isVisible():
            QMessageBox.information(self, "Time Tracker",
                                "The application will keep running in the system tray. "
                                "To terminate the program, choose 'Quit' in the context menu "
                                "of the system tray entry.")
            self.hide()
            event.ignore()
        else:
            self.close_application()