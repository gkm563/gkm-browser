import sys
import json
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QAction, QLineEdit, QFileDialog, QMessageBox, 
    QListWidget, QVBoxLayout, QWidget, QTabWidget, QMenu, QInputDialog, QPushButton, 
    QHBoxLayout, QComboBox
)
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineProfile, QWebEnginePage
from PyQt5.QtCore import QUrl, Qt, QEvent, QSize
from PyQt5.QtGui import QIcon, QPixmap, QImage
import datetime

# Paths for bookmarks, history, and settings
BOOKMARK_FILE = "bookmarks.json"
HISTORY_FILE = "history.json"
SETTINGS_FILE = "settings.json"
DOWNLOADS = []

# Available search engines
SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q={}",
    "Bing": "https://www.bing.com/search?q={}",
    "DuckDuckGo": "https://duckduckgo.com/?q={}"
}

class GKM_Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GKM Browser Pro 🌐")
        self.setGeometry(200, 100, 1200, 800)

        self.incognito_mode = False
        self.dark_mode_enabled = False
        self.ad_block_enabled = False
        self.bookmarks = self.load_bookmarks()
        self.history = self.load_history()
        self.settings = self.load_settings()
        self.search_engine = self.settings.get("search_engine", SEARCH_ENGINES["Google"])
        self.search_engine_name = self.settings.get("search_engine_name", "Google")
        self.homepage = self.settings.get("homepage", "https://google.com")

        # Tab widget for multiple tabs
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self.update_navigation_buttons)
        self.setCentralWidget(self.tab_widget)

        # Default profile for non-incognito mode
        self.default_profile = QWebEngineProfile.defaultProfile()
        self.add_new_tab(QUrl(self.homepage), "New Tab")
        
        self.create_navbar()
        self.create_menubar()

    def create_navbar(self):
        self.navbar = QToolBar()
        self.navbar.setIconSize(QSize(24, 24))
        self.addToolBar(self.navbar)

        # Navigation buttons with tooltips
        self.back_btn = QAction("←", self)
        self.back_btn.setToolTip("Back")
        self.back_btn.triggered.connect(lambda: self.current_browser().back())
        self.navbar.addAction(self.back_btn)

        self.forward_btn = QAction("→", self)
        self.forward_btn.setToolTip("Forward")
        self.forward_btn.triggered.connect(lambda: self.current_browser().forward())
        self.navbar.addAction(self.forward_btn)

        self.reload_btn = QAction("⟳", self)
        self.reload_btn.setToolTip("Reload")
        self.reload_btn.triggered.connect(lambda: self.current_browser().reload())
        self.navbar.addAction(self.reload_btn)

        # Zoom controls
        zoom_in_btn = QAction("🔍+", self)
        zoom_in_btn.setToolTip("Zoom In")
        zoom_in_btn.triggered.connect(self.zoom_in)
        self.navbar.addAction(zoom_in_btn)

        zoom_out_btn = QAction("🔍-", self)
        zoom_out_btn.setToolTip("Zoom Out")
        zoom_out_btn.triggered.connect(self.zoom_out)
        self.navbar.addAction(zoom_out_btn)

        zoom_reset_btn = QAction("🔍", self)
        zoom_reset_btn.setToolTip("Reset Zoom")
        zoom_reset_btn.triggered.connect(self.zoom_reset)
        self.navbar.addAction(zoom_reset_btn)

        # New tab button
        new_tab_btn = QAction("➕", self)
        new_tab_btn.setToolTip("New Tab")
        new_tab_btn.triggered.connect(lambda: self.add_new_tab(QUrl(self.homepage), "New Tab"))
        self.navbar.addAction(new_tab_btn)

        # Search engine selector
        self.search_engine_combo = QComboBox()
        self.search_engine_combo.setToolTip("Select Search Engine")
        self.search_engine_combo.setMaximumWidth(100)
        for engine in SEARCH_ENGINES:
            self.search_engine_combo.addItem(engine)
        self.search_engine_combo.setCurrentText(self.search_engine_name)
        self.search_engine_combo.currentTextChanged.connect(self.change_search_engine)
        self.navbar.addWidget(self.search_engine_combo)

        # URL bar
        self.url_bar = QLineEdit()
        self.url_bar.setToolTip("Enter URL or search query")
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        self.navbar.addWidget(self.url_bar)

        # Find in page
        self.find_bar = QLineEdit()
        self.find_bar.setPlaceholderText("Find in page...")
        self.find_bar.setMaximumWidth(200)
        self.find_bar.setToolTip("Search text on page")
        self.find_bar.returnPressed.connect(self.find_in_page)
        self.navbar.addWidget(self.find_bar)

        # Bookmark
        bookmark_btn = QAction("★", self)
        bookmark_btn.setToolTip("Add Bookmark")
        bookmark_btn.triggered.connect(self.add_bookmark)
        self.navbar.addAction(bookmark_btn)

        view_bookmarks_btn = QAction("📑", self)
        view_bookmarks_btn.setToolTip("View Bookmarks")
        view_bookmarks_btn.triggered.connect(self.show_bookmarks)
        self.navbar.addAction(view_bookmarks_btn)

        # History
        history_btn = QAction("🕒", self)
        history_btn.setToolTip("View History")
        history_btn.triggered.connect(self.show_history)
        self.navbar.addAction(history_btn)

        # Downloads
        download_btn = QAction("⬇", self)
        download_btn.setToolTip("View Downloads")
        download_btn.triggered.connect(self.show_downloads)
        self.navbar.addAction(download_btn)

        # Screenshot
        screenshot_btn = QAction("📸", self)
        screenshot_btn.setToolTip("Capture Screenshot")
        screenshot_btn.triggered.connect(self.capture_screenshot)
        self.navbar.addAction(screenshot_btn)

        # Ad blocker
        adblock_btn = QAction("🛑", self)
        adblock_btn.setToolTip("Toggle Ad Blocker")
        adblock_btn.triggered.connect(self.toggle_ad_block)
        self.navbar.addAction(adblock_btn)

        # Dark mode
        darkmode_btn = QAction("🌙", self)
        darkmode_btn.setToolTip("Toggle Dark Mode")
        darkmode_btn.triggered.connect(self.toggle_dark_mode)
        self.navbar.addAction(darkmode_btn)

        # Incognito mode
        incognito_btn = QAction("🕵️", self)
        incognito_btn.setToolTip("Toggle Incognito Mode")
        incognito_btn.triggered.connect(self.toggle_incognito_mode)
        self.navbar.addAction(incognito_btn)

    def create_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        
        new_tab_action = QAction("New Tab", self)
        new_tab_action.triggered.connect(lambda: self.add_new_tab(QUrl(self.homepage), "New Tab"))
        file_menu.addAction(new_tab_action)
        
        save_page_action = QAction("Save Page As...", self)
        save_page_action.triggered.connect(self.save_page)
        file_menu.addAction(save_page_action)
        
        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self.clear_history)
        file_menu.addAction(clear_history_action)
        
        set_homepage_action = QAction("Set Homepage", self)
        set_homepage_action.triggered.connect(self.set_homepage)
        file_menu.addAction(set_homepage_action)
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def current_browser(self):
        return self.tab_widget.currentWidget()

    def add_new_tab(self, url, title):
        browser = QWebEngineView()
        profile = QWebEngineProfile("incognito" if self.incognito_mode else "default", browser)
        page = QWebEnginePage(profile, browser)
        browser.setPage(page)
        browser.setUrl(url)
        
        index = self.tab_widget.addTab(browser, title)
        self.tab_widget.setCurrentIndex(index)
        
        browser.urlChanged.connect(lambda q: self.update_url(q, browser))
        browser.titleChanged.connect(lambda title: self.tab_widget.setTabText(self.tab_widget.indexOf(browser), title[:20]))
        if not self.incognito_mode:
            browser.urlChanged.connect(self.update_history)
        profile.downloadRequested.connect(self.handle_download)
        
        # Context menu
        browser.setContextMenuPolicy(Qt.CustomContextMenu)
        browser.customContextMenuRequested.connect(lambda pos: self.show_context_menu(pos, browser))
        
        # Apply ad blocker if enabled
        if self.ad_block_enabled:
            self.apply_ad_block(browser)

    def show_context_menu(self, pos, browser):
        menu = QMenu()
        copy_url_action = QAction("Copy URL", self)
        copy_url_action.triggered.connect(lambda: QApplication.clipboard().setText(browser.url().toString()))
        
        open_new_tab_action = QAction("Open in New Tab", self)
        open_new_tab_action.triggered.connect(lambda: self.add_new_tab(browser.url(), browser.title()))
        
        menu.addAction(copy_url_action)
        menu.addAction(open_new_tab_action)
        menu.exec_(browser.mapToGlobal(pos))

    def close_tab(self, index):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(index)
        else:
            QMessageBox.warning(self, "Warning", "Cannot close the last tab!")

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        
        # Check if it's a URL
        if text.startswith(("http://", "https://")) or "." in text:
            if not text.startswith(("http://", "https://")):
                text = "https://" + text
            self.current_browser().setUrl(QUrl(text))
        else:
            # Perform search with selected search engine
            search_url = self.search_engine.format(text.replace(" ", "+"))
            self.current_browser().setUrl(QUrl(search_url))

    def change_search_engine(self, engine_name):
        self.search_engine = SEARCH_ENGINES[engine_name]
        self.search_engine_name = engine_name
        self.settings["search_engine"] = self.search_engine
        self.settings["search_engine_name"] = engine_name
        self.save_settings()
        QMessageBox.information(self, "Search Engine", f"Search engine set to: {engine_name}")

    def update_url(self, q, browser):
        if browser == self.current_browser():
            self.url_bar.setText(q.toString())

    def update_history(self, q):
        if not self.incognito_mode:
            url = q.toString()
            timestamp = datetime.datetime.now().isoformat()
            self.history.append({"url": url, "timestamp": timestamp})
            self.save_history()

    def update_navigation_buttons(self, index):
        pass

    def load_bookmarks(self):
        if os.path.exists(BOOKMARK_FILE):
            try:
                with open(BOOKMARK_FILE, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
                    return []
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_bookmarks(self):
        try:
            with open(BOOKMARK_FILE, 'w') as f:
                json.dump(self.bookmarks, f)
        except IOError:
            QMessageBox.warning(self, "Error", "Failed to save bookmarks.")

    def add_bookmark(self):
        current_url = self.current_browser().url().toString()
        if current_url and not any(b["url"] == current_url for b in self.bookmarks):
            name, ok = QInputDialog.getText(self, "Bookmark Name", "Enter name for bookmark:", text=current_url)
            if ok and name:
                self.bookmarks.append({"name": name, "url": current_url})
                self.save_bookmarks()
                QMessageBox.information(self, "Bookmark Added", f"Bookmarked: {name}")

    def show_bookmarks(self):
        dialog = QWidget(self)
        dialog.setWindowTitle("Bookmarks")
        layout = QVBoxLayout()
        list_widget = QListWidget()
        for bookmark in self.bookmarks:
            list_widget.addItem(bookmark["name"])
        list_widget.itemDoubleClicked.connect(
            lambda item: self.current_browser().setUrl(QUrl(self.bookmarks[list_widget.row(item)]["url"]))
        )
        layout.addWidget(list_widget)
        dialog.setLayout(layout)
        dialog.resize(400, 300)
        dialog.show()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
                    return []
            except (json.JSONDecodeError, IOError):
                return []
        return []

    def save_history(self):
        try:
            with open(HISTORY_FILE, 'w') as f:
                json.dump(self.history, f)
        except IOError:
            QMessageBox.warning(self, "Error", "Failed to save history.")

    def show_history(self):
        dialog = QWidget(self)
        dialog.setWindowTitle("History")
        layout = QVBoxLayout()
        list_widget = QListWidget()
        for entry in reversed(self.history):
            list_widget.addItem(f"{entry['timestamp']} - {entry['url']}")
        list_widget.itemDoubleClicked.connect(
            lambda item: self.current_browser().setUrl(QUrl(self.history[len(self.history) - 1 - list_widget.row(item)]['url']))
        )
        layout.addWidget(list_widget)
        dialog.setLayout(layout)
        dialog.resize(600, 400)
        dialog.show()

    def clear_history(self):
        reply = QMessageBox.question(self, "Clear History", "Are you sure you want to clear your browsing history?",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.history = []
            self.save_history()
            QMessageBox.information(self, "History Cleared", "Browsing history has been cleared.")

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
                    return {}
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(self.settings, f)
        except IOError:
            QMessageBox.warning(self, "Error", "Failed to save settings.")

    def set_homepage(self):
        url, ok = QInputDialog.getText(self, "Set Homepage", "Enter homepage URL:", text=self.homepage)
        if ok and url:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            self.settings["homepage"] = url
            self.homepage = url
            self.save_settings()
            QMessageBox.information(self, "Homepage Set", f"Homepage set to: {url}")

    def show_downloads(self):
        dialog = QWidget(self)
        dialog.setWindowTitle("Downloads")
        layout = QVBoxLayout()
        list_widget = QListWidget()
        if not DOWNLOADS:
            list_widget.addItem("No downloads yet")
        else:
            for download in DOWNLOADS:
                list_widget.addItem(f"{download['path']} - {download['status']}")
        layout.addWidget(list_widget)
        dialog.setLayout(layout)
        dialog.resize(400, 300)
        dialog.show()

    def handle_download(self, download):
        suggested_path = download.suggestedFileName()
        path, _ = QFileDialog.getSaveFileName(self, "Save File", suggested_path)
        if path:
            download.setPath(path)
            download.accept()
            DOWNLOADS.append({"path": path, "status": "In Progress"})
            download.finished.connect(lambda: self.update_download_status(path, "Completed"))
            download.downloadProgress.connect(lambda received, total: self.update_download_progress(path, received, total))
            QMessageBox.information(self, "Download", f"Downloading to: {path}")

    def update_download_status(self, path, status):
        for download in DOWNLOADS:
            if download["path"] == path:
                download["status"] = status
                break

    def update_download_progress(self, path, received, total):
        for download in DOWNLOADS:
            if download["path"] == path:
                download["status"] = f"Progress: {received}/{total} bytes"
                break

    def save_page(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Page", "", "Web Page (*.html);;All Files (*)")
        if path:
            self.current_browser().page().toHtml(lambda html: self.save_html(path, html))

    def save_html(self, path, html):
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            QMessageBox.information(self, "Success", "Page saved successfully!")
        except IOError:
            QMessageBox.warning(self, "Error", "Failed to save page.")

    def capture_screenshot(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Screenshot", "", "PNG Image (*.png);;All Files (*)")
        if path:
            self.current_browser().grab().save(path, "PNG")
            QMessageBox.information(self, "Success", f"Screenshot saved to: {path}")

    def toggle_ad_block(self):
        self.ad_block_enabled = not self.ad_block_enabled
        for i in range(self.tab_widget.count()):
            browser = self.tab_widget.widget(i)
            self.apply_ad_block(browser)
        status = "enabled" if self.ad_block_enabled else "disabled"
        QMessageBox.information(self, "Ad Blocker", f"Ad blocker {status}!")

    def apply_ad_block(self, browser):
        ad_block_script = """
        (function() {
            var ads = document.querySelectorAll('[id*="ad"], [class*="ad"], [id*="banner"], [class*="banner"]');
            ads.forEach(ad => ad.style.display = 'none');
        })();
        """ if self.ad_block_enabled else ""
        browser.page().runJavaScript(ad_block_script)

    def find_in_page(self):
        text = self.find_bar.text().strip()
        if text:
            self.current_browser().findText(text, QWebEnginePage.FindFlags(), lambda result: self.find_result(result))

    def find_result(self, found):
        if not found:
            QMessageBox.information(self, "Find", "Text not found on page.")

    def toggle_dark_mode(self):
        self.dark_mode_enabled = not self.dark_mode_enabled
        script = "document.body.style.filter = 'invert(1) hue-rotate(180deg)'" if self.dark_mode_enabled else "document.body.style.filter = ''"
        self.current_browser().page().runJavaScript(script)

    def toggle_incognito_mode(self):
        self.incognito_mode = not self.incognito_mode
        message = "Incognito mode enabled!" if self.incognito_mode else "Incognito mode disabled!"
        QMessageBox.information(self, "Incognito", message)
        self.add_new_tab(QUrl(self.homepage), "New Tab")

    def zoom_in(self):
        current_zoom = self.current_browser().zoomFactor()
        self.current_browser().setZoomFactor(current_zoom + 0.1)

    def zoom_out(self):
        current_zoom = self.current_browser().zoomFactor()
        self.current_browser().setZoomFactor(max(0.1, current_zoom - 0.1))

    def zoom_reset(self):
        self.current_browser().setZoomFactor(1.0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("GKM Browser Pro")
    window = GKM_Browser()
    window.show()
    sys.exit(app.exec_())