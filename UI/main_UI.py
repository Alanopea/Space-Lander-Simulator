import sys
from PyQt5.QtWidgets import QApplication
from dashboard_UI import Dashboard

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec_())