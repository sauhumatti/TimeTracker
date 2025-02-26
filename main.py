import sys
from PyQt5.QtWidgets import QApplication
from time_tracker_app import TimeTrackerApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TimeTrackerApp()
    window.show()
    sys.exit(app.exec_())
