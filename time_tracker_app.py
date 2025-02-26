from PyQt5.QtWidgets import (QMainWindow, QTreeWidget, QTreeWidgetItem, QPushButton, 
                             QLabel, QVBoxLayout, QHBoxLayout, QWidget, QTableWidgetItem,
                             QSystemTrayIcon, QMenu, QAction, QDialog, QLineEdit,
                             QTextEdit, QComboBox, QMessageBox, QInputDialog, QApplication,
                             QFrame, QSplitter, QHeaderView, QStyleFactory)

from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QIcon, QColor, QPalette, QFont, QBrush, QLinearGradient, QGradient, QPainter
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal, QPropertyAnimation, QEasingCurve

from database_manager import DatabaseManager
from window_tracker import WindowTracker

import datetime
from collections import defaultdict
import sys
import os

class TimeTrackerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set the application style and theme
        self.setup_theme()
        
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
    
    def setup_theme(self):
        """Setup the application theme and styling"""
        # Use Fusion style for a modern look
        QApplication.setStyle(QStyleFactory.create("Fusion"))
        
        # Create a custom dark palette
        palette = QPalette()
        
        # Set colors for various UI elements
        palette.setColor(QPalette.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.AlternateBase, QColor(66, 66, 66))
        palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        palette.setColor(QPalette.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        # Apply the palette
        QApplication.setPalette(palette)
    
    def init_ui(self):
        """Initialize the UI components"""
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Create a header with app title
        header = QLabel("TimeTracker")
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Bold))
        header.setStyleSheet("color: #4FC3F7; margin-bottom: 10px;")
        main_layout.addWidget(header)
        
        # Create a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #555; max-height: 1px;")
        main_layout.addWidget(separator)
        
        # Create project selection area
        project_frame = QFrame()
        project_frame.setStyleSheet("background-color: #333; border-radius: 5px; padding: 8px;")
        project_layout = QHBoxLayout(project_frame)
        project_layout.setContentsMargins(10, 10, 10, 10)
        
        # Project label and combo box
        project_label = QLabel("Project:")
        project_label.setStyleSheet("font-weight: bold; color: #4FC3F7;")
        project_layout.addWidget(project_label)
        
        self.project_combo = QComboBox()
        self.project_combo.setMinimumWidth(200)
        self.project_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                background-color: #3C3C3C;
                color: white;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 15px;
                border-left: 1px solid #555;
            }
        """)
        self.project_combo.currentIndexChanged.connect(self.on_project_changed)
        project_layout.addWidget(self.project_combo)
        
        # Project management buttons
        button_style = """
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """
        
        self.new_project_btn = QPushButton("New Project")
        self.new_project_btn.setStyleSheet(button_style + "background-color: #2196F3;")
        self.new_project_btn.clicked.connect(self.create_project_dialog)
        project_layout.addWidget(self.new_project_btn)
        
        self.edit_project_btn = QPushButton("Edit")
        self.edit_project_btn.setStyleSheet(button_style)
        self.edit_project_btn.clicked.connect(self.edit_project_dialog)
        project_layout.addWidget(self.edit_project_btn)
        
        self.delete_project_btn = QPushButton("Delete")
        self.delete_project_btn.setStyleSheet(button_style)
        self.delete_project_btn.clicked.connect(self.delete_project_dialog)
        project_layout.addWidget(self.delete_project_btn)
        
        main_layout.addWidget(project_frame)
        
        # Create tracking control area
        tracking_frame = QFrame()
        tracking_frame.setStyleSheet("background-color: #333; border-radius: 5px; padding: 8px;")
        tracking_layout = QHBoxLayout(tracking_frame)
        tracking_layout.setContentsMargins(10, 10, 10, 10)
        
        self.tracking_btn = QPushButton("Start Tracking")
        self.tracking_btn.setMinimumHeight(40)
        self.tracking_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                font-weight: bold;
                border-radius: 3px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #66BB6A;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
        """)
        self.tracking_btn.clicked.connect(self.toggle_tracking)
        tracking_layout.addWidget(self.tracking_btn)
        
        self.tracking_status = QLabel("Tracking stopped")
        self.tracking_status.setStyleSheet("color: #EF5350; font-style: italic;")
        tracking_layout.addWidget(self.tracking_status)
        tracking_layout.addStretch()
        
        main_layout.addWidget(tracking_frame)
        
        # Create activity tree widget
        activity_label = QLabel("Today's Activities")
        activity_label.setStyleSheet("color: #4FC3F7; font-weight: bold; font-size: 14px; margin-top: 10px;")
        activity_label.setAlignment(Qt.AlignLeft)
        main_layout.addWidget(activity_label)
        
        self.activity_table = QTreeWidget()
        self.activity_table.setColumnCount(2)
        self.activity_table.setHeaderLabels(["Application", "Duration"])
        self.activity_table.setAlternatingRowColors(True)
        self.activity_table.setStyleSheet("""
            QTreeWidget {
                background-color: #2D2D2D;
                alternate-background-color: #353535;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
                color: white;
            }
            QTreeWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444;
            }
            QTreeWidget::item:selected {
                background-color: #2196F3;
            }
            QHeaderView::section {
                background-color: #333;
                padding: 6px;
                border: 1px solid #555;
                color: white;
                font-weight: bold;
            }
        """)
        self.activity_table.header().setStretchLastSection(True)
        self.activity_table.setColumnWidth(0, 300)
        self.activity_table.itemClicked.connect(self.on_item_clicked)
        self.activity_table.setAnimated(True)
        self.activity_table.setIndentation(20)
        self.activity_table.header().setSectionResizeMode(QHeaderView.Interactive)
        
        main_layout.addWidget(self.activity_table)
        
        # Set the main layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
        # Set window properties
        self.setWindowTitle("TimeTracker - Productivity Analyzer")
        self.setGeometry(100, 100, 900, 700)
    
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
        dialog.setStyleSheet("""
            QDialog {
                background-color: #333;
                color: white;
            }
            QLabel {
                color: white;
                font-weight: bold;
                margin-top: 5px;
            }
            QLineEdit, QTextEdit {
                background-color: #444;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 3px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #555;
            }
            QPushButton:pressed {
                background-color: #333;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("Create New Project")
        header.setStyleSheet("font-size: 16px; color: #4FC3F7; margin-bottom: 15px;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #555; max-height: 1px; margin-bottom: 15px;")
        layout.addWidget(separator)
        
        name_label = QLabel("Project Name:")
        layout.addWidget(name_label)
        
        name_input = QLineEdit()
        name_input.setPlaceholderText("Enter project name...")
        layout.addWidget(name_input)
        
        desc_label = QLabel("Description:")
        layout.addWidget(desc_label)
        
        desc_input = QTextEdit()
        desc_input.setMaximumHeight(100)
        desc_input.setPlaceholderText("Enter project description...")
        layout.addWidget(desc_input)
        
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 20, 0, 0)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        create_btn = QPushButton("Create")
        create_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #42A5F5;
            }
            QPushButton:pressed {
                background-color: #1E88E5;
            }
        """)
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
            self.tracking_btn.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-weight: bold;
                    border-radius: 3px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #EF5350;
                }
                QPushButton:pressed {
                    background-color: #D32F2F;
                }
            """)
            self.tracking_status.setText("Tracking active...")
            self.tracking_status.setStyleSheet("color: #4CAF50; font-style: italic;")
        else:
            self.window_tracker.stop_tracking()
            self.tracking_btn.setText("Start Tracking")
            self.tracking_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    font-weight: bold;
                    border-radius: 3px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #66BB6A;
                }
                QPushButton:pressed {
                    background-color: #388E3C;
                }
            """)
            self.tracking_status.setText("Tracking stopped")
            self.tracking_status.setStyleSheet("color: #EF5350; font-style: italic;")
    
    def on_activity_changed(self, activity):
        """Handle activity change event from tracker"""
        # Add project_id to activity before saving
        activity["project_id"] = self.current_project_id
        # Save the activity to the database
        self.db_manager.save_activity(activity)
        
        # Update status with styled text and refresh view
        status_text = f"Tracking: {activity['name']} - {activity['short_title']}"
        self.tracking_status.setText(status_text)
        self.tracking_status.setStyleSheet("""
            color: #4CAF50;
            font-style: italic;
            background-color: rgba(76, 175, 80, 0.1);
            border-radius: 3px;
            padding: 3px;
        """)
        self.update_activity_display()
    
    def update_activity_display(self):
        """Update the activity display with hierarchical data"""
        # Store the expanded state before clearing
        expanded_apps = {}
        expanded_domains = {}
        
        # Save expanded state
        root = self.activity_table.invisibleRootItem()
        for i in range(root.childCount()):
            app_item = root.child(i)
            app_name = app_item.text(0)
            if app_item.isExpanded():
                expanded_apps[app_name] = True
                
                # Save expanded state of domains
                for j in range(app_item.childCount()):
                    domain_item = app_item.child(j)
                    domain_name = domain_item.text(0)
                    key = f"{app_name}|{domain_name}"
                    if domain_item.isExpanded():
                        expanded_domains[key] = True
        
        # Clear and rebuild the tree
        self.activity_table.clear()
        
        if not self.db_manager:
            return
        
        # Get hierarchical activity data
        activities = self.db_manager.get_today_activities_hierarchical(self.current_project_id)
        
        # Font settings
        app_font = QFont()
        app_font.setBold(True)
        app_font.setPointSize(10)
        
        domain_font = QFont()
        domain_font.setBold(True)
        domain_font.setPointSize(9)
        
        for app_data in activities:
            # Create app-level item
            app_item = QTreeWidgetItem(self.activity_table)
            app_name = app_data["name"]
            app_item.setText(0, app_name)
            app_item.setText(1, app_data["duration_formatted"])
            app_item.setData(0, Qt.UserRole, "app")  # Tag as an app item
            
            # Style the app item
            app_item.setFont(0, app_font)
            app_item.setForeground(0, QBrush(QColor("#4FC3F7")))  # Light blue
            app_item.setForeground(1, QBrush(QColor("#4FC3F7")))
            
            # Restore app expansion state
            if app_name in expanded_apps:
                app_item.setExpanded(True)
            
            # Show child items for all applications
            if app_data["children"]:
                for domain in app_data["children"]:
                    # Create domain-level item
                    domain_item = QTreeWidgetItem(app_item)
                    domain_name = domain["domain_info"]
                    domain_item.setText(0, domain_name)
                    domain_item.setText(1, domain["duration_formatted"])
                    domain_item.setData(0, Qt.UserRole, "domain")  # Tag as a domain item
                    
                    # Style the domain item
                    domain_item.setFont(0, domain_font)
                    domain_item.setForeground(0, QBrush(QColor("#FFD54F")))  # Light amber
                    domain_item.setForeground(1, QBrush(QColor("#FFD54F")))
                    
                    # Restore domain expansion state
                    key = f"{app_name}|{domain_name}"
                    if key in expanded_domains:
                        domain_item.setExpanded(True)
                    
                    # Add individual websites/window titles under domain
                    if "children" in domain:
                        for website in domain["children"]:
                            # Create website-level item
                            site_item = QTreeWidgetItem(domain_item)
                            site_item.setText(0, website["window_title"])
                            site_item.setText(1, website["duration_formatted"])
                            site_item.setData(0, Qt.UserRole, "website")  # Tag as a website item
                            
                            # Style the website item
                            site_item.setForeground(0, QBrush(QColor("#FFFFFF")))  # White
                            site_item.setForeground(1, QBrush(QColor("#AAAAAA")))  # Light gray
        
        # Set column widths
        self.activity_table.setColumnWidth(0, 400)

    def on_item_clicked(self, item, column):
        """Handle clicks on tree items to expand/collapse"""
        item_type = item.data(0, Qt.UserRole)
        
        # Handle any expandable items (app and domain)
        if item_type in ["app", "domain"]:
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