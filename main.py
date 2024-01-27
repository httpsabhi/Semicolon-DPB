import sys
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QWidget, QVBoxLayout, QLabel, QDialog
from PyQt5.QtWidgets import QSizePolicy, QPushButton
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebEngineWidgets import QWebEngineView
import requests
from bs4 import BeautifulSoup

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.google.com"))

        self.setCentralWidget(self.browser)

        self.create_toolbar()

        self.showMaximized()
        self.setWindowTitle("Web Browser")

    def create_toolbar(self):
        navbar = QToolBar()
        self.addToolBar(navbar)

        actions = [
            ("Back", self.browser.back),
            ("Forward", self.browser.forward),
            ("Reload", self.browser.reload),
            ("Home", self.navigate_home),
            ("Scrape", self.scrape_current_page)
        ]

        for action_text, method in actions:
            action = QAction(action_text, self)
            action.setStatusTip(f"{action_text} page")
            action.triggered.connect(method)
            navbar.addAction(action)

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        navbar.addSeparator()

        open_browser_action = QAction("Open in Default Browser", self)
        open_browser_action.triggered.connect(self.open_in_default_browser)
        navbar.addAction(open_browser_action)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)
        navbar.addAction(about_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_application)
        navbar.addAction(quit_action)

        # Add a button to manually trigger scraping
        scrape_button = QPushButton("Scrape")
        scrape_button.clicked.connect(self.scrape_current_page)
        navbar.addWidget(scrape_button)

        navbar.addSeparator()
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        navbar.addWidget(spacer)

    def navigate_home(self):
        self.browser.setUrl(QUrl("https://www.google.com"))

    def navigate_to_url(self):
        q = QUrl(self.url_bar.text())
        if q.scheme() == "":
            q.setScheme("http")
        self.browser.setUrl(q)

    def open_in_default_browser(self):
        QDesktopServices.openUrl(self.browser.url())

    def show_about_dialog(self):
        self.show_info_dialog("About Web Browser", "Simple web browser using Python and PyQt5.")

    def quit_application(self):
        QApplication.quit()

    def scrape_current_page(self):
        current_url = self.browser.url().toString()
        if current_url:
            self.scrape_url(current_url)

    def scrape_url(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            form = soup.find('form')

            if form:
                input_fields = form.find_all('input')

                required_fields = []
                non_required_fields = []

                for input_field in input_fields:
                    field_label = input_field.get('aria-label') or input_field.get('placeholder') or input_field.get('name')
                    field_value = input_field.get('value')
                    is_required = 'required' in input_field.attrs

                    if is_required:
                        required_fields.append((field_label, field_value))
                    else:
                        non_required_fields.append((field_label, field_value))

                self.show_scrape_results(required_fields, non_required_fields)

            else:
                self.show_warning_dialog("Scraping Error", "No form found on the page.")

        else:
            self.show_warning_dialog("Scraping Error", f"Failed to fetch the webpage. Status code: {response.status_code}")

    def show_scrape_results(self, required_fields, non_required_fields):
        dialog = QDialog(self)
        dialog.setWindowTitle("Scraping Results")

        layout = QVBoxLayout()

        required_label = QLabel("Required Fields:")
        layout.addWidget(required_label)

        for field_label, field_value in required_fields:
            field_label = QLabel(f"{field_label}: {field_value}")
            layout.addWidget(field_label)

        non_required_label = QLabel("\nNon-Required Fields:")
        layout.addWidget(non_required_label)

        for field_label, field_value in non_required_fields:
            field_label = QLabel(f"{field_label}: {field_value}")
            layout.addWidget(field_label)

        dialog.setLayout(layout)
        dialog.exec_()

    def show_info_dialog(self, title, message):
        QMessageBox.information(self, title, message)

    def show_warning_dialog(self, title, message):
        QMessageBox.warning(self, title, message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Web Browser")
    QApplication.setOrganizationName("YourOrganization")
    QApplication.setOrganizationDomain("yourorganization.com")

    window = Browser()
    sys.exit(app.exec_())
