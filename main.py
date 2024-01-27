import sys
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QDialog, QVBoxLayout, QLabel, QMessageBox
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWebEngineWidgets import QWebEngineView

import requests
from bs4 import BeautifulSoup
import nltk
import pickle
from nltk.corpus import stopwords
import string
from nltk.stem.porter import PorterStemmer

nltk.download('punkt')

ps = PorterStemmer()

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        self.tabs = []

        self.create_toolbar()
        self.add_tab()  # Open the initial tab

        self.showMaximized()
        self.setWindowTitle("Web Browser")

        # Load the pickled models
        self.cv = pickle.load(open('countvectorizer.pkl', 'rb'))
        self.tfidf = pickle.load(open('vectorizer.pkl', 'rb'))
        self.mnb = pickle.load(open('model.pkl', 'rb'))

    def create_toolbar(self):
        navbar = QToolBar()
        self.addToolBar(navbar)

        actions = [
            ("Back", self.navigate_back),
            ("Forward", self.navigate_forward),
            ("Reload", self.navigate_reload),
            ("Home", self.navigate_home),
            ("Scrape", self.scrape_current_page),
            ("New Tab", self.add_tab)
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

    def navigate_back(self):
        self.current_browser().back()

    def navigate_forward(self):
        self.current_browser().forward()

    def navigate_reload(self):
        self.current_browser().reload()

    def navigate_home(self):
        self.current_browser().setUrl(QUrl("https://www.google.com"))

    def navigate_to_url(self):
        q = QUrl(self.url_bar.text())
        if q.scheme() == "":
            q.setScheme("http")
        self.current_browser().setUrl(q)

    def open_in_default_browser(self):
        QDesktopServices.openUrl(self.current_browser().url())

    def show_about_dialog(self):
        QMessageBox.about(self, "About Web Browser", "Simple web browser using Python and PyQt5.")

    def quit_application(self):
        QApplication.quit()

    def add_tab(self):
        browser = QWebEngineView()
        browser.setUrl(QUrl("https://www.google.com"))
        self.tabs.append(browser)
        self.setCentralWidget(browser)
        self.url_bar.setText("")
        browser.urlChanged.connect(lambda qurl, browser=browser: self.update_urlbar(qurl, browser))

    def current_browser(self):
        if self.tabs:
            return self.tabs[-1]
        else:
            return None

    def update_urlbar(self, q, browser=None):
        if browser != self.current_browser():
            return
        self.url_bar.setText(q.toString())
        self.url_bar.setCursorPosition(0)

    def scrape_current_page(self):
        current_url = self.current_browser().url().toString()
        if current_url:
            self.scrape_url(current_url)

    def transform_text(self, text):
        text = text.lower()
        text = nltk.word_tokenize(text)

        y = []
        for i in text:
            if i.isalnum():
                y.append(i)

        text = y[:]
        y.clear()

        for i in text:
            if i not in stopwords.words('english') and i not in string.punctuation:
                y.append(i)

        text = y[:]
        y.clear()

        for i in text:
            y.append(ps.stem(i))

        return " ".join(y)

    def scrape_url(self, url):
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            self.spam_check(soup)
            self.form_check(soup)

        else:
            QMessageBox.warning(self, "Scraping Error", f"Failed to fetch the webpage. Status code: {response.status_code}")

    def spam_check(self, soup):
        try:
            text_content = soup.get_text()
            text = self.transform_text(text_content)
            cv_input = self.cv.transform([text])
            vector_input = self.tfidf.transform(cv_input)
            result = self.mnb.predict(vector_input)[0]

            if result == 1:
                QMessageBox.warning(self, "Spam Check", "Potential spam detected on the webpage!")
            else:
                QMessageBox.information(self, "Spam Check", "No spam detected on the webpage.")
        except Exception as e:
            QMessageBox.warning(self, "Spam Check Error", f"Error during spam check: {str(e)}")

    def form_check(self, soup):
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
            QMessageBox.warning(self, "Form Check", "No form found on the page.")

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("SemiWeb")
    QApplication.setOrganizationName("SemiColon")
    QApplication.setOrganizationDomain("semicolon.com")

    window = Browser()
    sys.exit(app.exec_())
