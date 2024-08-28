import sys
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *
from PyQt5.QtGui import QIcon
import requests  # For using an API to summarize text, detect emotion, and perform fact-checking

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("https://www.google.com"))
        self.setCentralWidget(self.browser)
        self.showMaximized()

        # Navigation Bar
        nav_bar = QToolBar()
        self.addToolBar(nav_bar)

        # Back Button
        back_btn = QAction(QIcon('back.png'), 'Back', self)
        back_btn.triggered.connect(self.browser.back)
        nav_bar.addAction(back_btn)

        # Forward Button
        forward_btn = QAction(QIcon('forward.png'), 'Forward', self)
        forward_btn.triggered.connect(self.browser.forward)
        nav_bar.addAction(forward_btn)

        # Reload Button
        reload_btn = QAction(QIcon('reload.png'), 'Reload', self)
        reload_btn.triggered.connect(self.browser.reload)
        nav_bar.addAction(reload_btn)

        # Home Button
        home_btn = QAction(QIcon('home.png'), 'Home', self)
        home_btn.triggered.connect(self.navigate_home)
        nav_bar.addAction(home_btn)

        # Dark Mode Toggle
        dark_mode_btn = QAction('Toggle Dark Mode', self)
        dark_mode_btn.triggered.connect(self.toggle_dark_mode)
        nav_bar.addAction(dark_mode_btn)

        # URL Bar
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        # Bookmark Button
        bookmark_btn = QAction(QIcon('bookmark.png'), 'Bookmark', self)
        bookmark_btn.triggered.connect(self.add_bookmark)
        nav_bar.addAction(bookmark_btn)

        # History Button
        history_btn = QAction(QIcon('history.png'), 'History', self)
        history_btn.triggered.connect(self.show_history)
        nav_bar.addAction(history_btn)

        # Download Manager
        self.browser.page().profile().downloadRequested.connect(self.download_requested)

        # History and Bookmarks
        self.history = []
        self.bookmarks = []
        self.downloads = []

        # Custom Context Menu
        self.browser.setContextMenuPolicy(Qt.CustomContextMenu)
        self.browser.customContextMenuRequested.connect(self.context_menu)

        # Dark Mode Flag
        self.dark_mode_enabled = False

        # Summarizer Tab
        self.summarizer_btn = QAction('Summarize Selected Text', self)
        self.summarizer_btn.triggered.connect(self.summarize_text)
        nav_bar.addAction(self.summarizer_btn)

        # Emotion Detection Tab (Replaces Sentiment Analysis)
        self.emotion_btn = QAction('Detect Emotion', self)
        self.emotion_btn.triggered.connect(self.detect_emotion)
        nav_bar.addAction(self.emotion_btn)

        # Fact-Checking Tab
        self.fact_check_btn = QAction('Fact-Check', self)
        self.fact_check_btn.triggered.connect(self.fact_check_text)
        nav_bar.addAction(self.fact_check_btn)

        # Connect loadFinished to apply dark mode after the page is fully loaded
        self.browser.loadFinished.connect(self.apply_dark_mode)

    def navigate_home(self):
        self.browser.setUrl(QUrl("https://www.google.com"))

    def navigate_to_url(self):
        url = self.url_bar.text()
        self.browser.setUrl(QUrl(url))

    def update_url(self, q):
        self.url_bar.setText(q.toString())
        self.history.append(q.toString())

    def add_bookmark(self):
        url = self.browser.url().toString()
        self.bookmarks.append(url)
        QMessageBox.information(self, "Bookmark Added", f"{url} has been added to bookmarks.")

    def show_history(self):
        history_dialog = QDialog(self)
        history_dialog.setWindowTitle('History')
        history_dialog.setGeometry(300, 300, 400, 300)

        layout = QVBoxLayout()
        history_list = QListWidget()
        history_list.addItems(self.history)

        history_list.itemClicked.connect(lambda item: self.browser.setUrl(QUrl(item.text())))

        layout.addWidget(history_list)
        history_dialog.setLayout(layout)
        history_dialog.exec_()

    def context_menu(self, point):
        menu = QMenu()

        back_action = QAction("Back", self)
        back_action.triggered.connect(self.browser.back)
        menu.addAction(back_action)

        forward_action = QAction("Forward", self)
        forward_action.triggered.connect(self.browser.forward)
        menu.addAction(forward_action)

        reload_action = QAction("Reload", self)
        reload_action.triggered.connect(self.browser.reload)
        menu.addAction(reload_action)

        bookmark_action = QAction("Add to Bookmarks", self)
        bookmark_action.triggered.connect(self.add_bookmark)
        menu.addAction(bookmark_action)

        summarize_action = QAction("Summarize Text", self)
        summarize_action.triggered.connect(self.summarize_text)
        menu.addAction(summarize_action)

        emotion_action = QAction("Detect Emotion", self)
        emotion_action.triggered.connect(self.detect_emotion)
        menu.addAction(emotion_action)

        fact_check_action = QAction("Fact-Check", self)
        fact_check_action.triggered.connect(self.fact_check)
        menu.addAction(fact_check_action)

        menu.exec_(self.browser.mapToGlobal(point))

    def toggle_dark_mode(self):
        self.dark_mode_enabled = not self.dark_mode_enabled
        self.apply_dark_mode()

    def apply_dark_mode(self):
        if self.dark_mode_enabled:
            self.browser.page().runJavaScript("""
                document.body.style.backgroundColor = '#121212';
                document.body.style.color = '#e0e0e0';
                document.querySelectorAll('*').forEach(e => {
                    e.style.backgroundColor = '#121212';
                    e.style.color = '#e0e0e0';
                });
            """)
            self.setStyleSheet("background-color: #121212; color: #e0e0e0;")
        else:
            self.browser.page().runJavaScript("""
                document.body.style.backgroundColor = '';
                document.body.style.color = '';
                document.querySelectorAll('*').forEach(e => {
                    e.style.backgroundColor = '';
                    e.style.color = '';
                });
            """)
            self.setStyleSheet("")

    def download_requested(self, item):
        path, _ = QFileDialog.getSaveFileName(self, "Save File", item.suggestedFileName())
        if path:
            item.setPath(path)
            item.accept()
            self.downloads.append(item)
            item.finished.connect(lambda: QMessageBox.information(self, "Download Finished", f"Downloaded: {path}"))

    def summarize_text(self):
        self.browser.page().runJavaScript("window.getSelection().toString();", self.display_summary)

    def display_summary(self, selected_text):
        if selected_text.strip():
            summary = self.summarize_via_api(selected_text)
            summary_dialog = QDialog(self)
            summary_dialog.setWindowTitle("Summary")
            summary_dialog.setGeometry(300, 300, 400, 300)

            layout = QVBoxLayout()
            summary_label = QLabel(summary)
            summary_label.setWordWrap(True)

            layout.addWidget(summary_label)
            summary_dialog.setLayout(layout)

            summary_dialog.exec_()
        else:
            QMessageBox.warning(self, "No Text Selected", "Please select text to summarize.")

    def summarize_via_api(self, text):
        # Replace this with your API key and endpoint
        api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        api_key = "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"
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"inputs": text}

        response = requests.post(api_url, json=data, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            if isinstance(response_data, list) and len(response_data) > 0:
                return response_data[0].get("summary_text", "No summary available.")
            else:
                return "No summary available."
        else:
            return f"Error: Unable to summarize text. Status code: {response.status_code}"

    def detect_emotion(self):
        self.browser.page().runJavaScript("window.getSelection().toString();", self.display_emotion)

    def display_emotion(self, selected_text):
        if selected_text.strip():
            emotion = self.emotion_via_api(selected_text)
            emotion_dialog = QDialog(self)
            emotion_dialog.setWindowTitle("Emotion Detection")
            emotion_dialog.setGeometry(300, 300, 400, 200)

            layout = QVBoxLayout()
            emotion_label = QLabel(emotion)
            emotion_label.setWordWrap(True)

            layout.addWidget(emotion_label)
            emotion_dialog.setLayout(layout)

            emotion_dialog.exec_()
        else:
            QMessageBox.warning(self, "No Text Selected", "Please select text to detect emotion.")

    def emotion_via_api(self, text):
        # Replace this with your API key and endpoint
        api_url = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
        api_key = "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"
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"inputs": text}

        response = requests.post(api_url, json=data, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            if isinstance(response_data, list) and len(response_data) > 0:
                emotions = response_data[0].get("label", "No emotion detected.")
                return f"Detected Emotion: {emotions}"
            else:
                return "No emotion detected."
        else:
            return f"Error: Unable to detect emotion. Status code: {response.status_code}"

    def fact_check_text(self):
        self.browser.page().runJavaScript("window.getSelection().toString();", self.display_fact_check)

    def display_fact_check(self, selected_text):
        if selected_text.strip():
            fact_check_result = self.fact_check_via_api(selected_text)
            fact_check_dialog = QDialog(self)
            fact_check_dialog.setWindowTitle("Fact Check")
            fact_check_dialog.setGeometry(300, 300, 400, 300)

            layout = QVBoxLayout()
            fact_check_label = QLabel(fact_check_result)
            fact_check_label.setWordWrap(True)

            layout.addWidget(fact_check_label)
            fact_check_dialog.setLayout(layout)

            fact_check_dialog.exec_()
        else:
            QMessageBox.warning(self, "No Text Selected", "Please select text to fact-check.")

    def fact_check_via_api(self, text):
        # Replace this with your API key and endpoint
        api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-mnli"
        api_key = "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"
        headers = {"Authorization": f"Bearer {api_key}"}
        data = {"inputs": text, "candidate_labels": ["true", "false"]}

        response = requests.post(api_url, json=data, headers=headers)

        if response.status_code == 200:
            response_data = response.json()
            if "labels" in response_data and len(response_data["labels"]) > 0:
                label = response_data["labels"][0]
                score = response_data["scores"][0]
                return f"Fact Check: {label.capitalize()} (Confidence: {score:.2f})"
            else:
                return "Unable to fact-check."
        else:
            return f"Error: Unable to fact-check text. Status code: {response.status_code}"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Skibidi Web Browser")
    window = Browser()
    app.exec_()
