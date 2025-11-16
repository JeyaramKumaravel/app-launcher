import sys
import os
import json
import subprocess
import shutil
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QLabel, QFileDialog,
    QMessageBox, QFrame, QSpacerItem, QSizePolicy, QDialog,
    QDialogButtonBox, QSystemTrayIcon, QMenu, QStyle,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QAction, QShortcut, QKeySequence, QPalette, QColor
)
from PyQt6.QtCore import (
    Qt, QSize, QEvent, QPropertyAnimation
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect

CONFIG_FILE = "apps.json"
ICON_DIR = "icons"


# ---------------- Helpers ----------------

def open_file_cross_platform(path: str):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def fuzzy_score(name: str, query: str) -> int:
    name_l = name.lower()
    q = query.lower()
    if not q:
        return 0
    score = 0
    if q in name_l:
        score += 100
    i = 0
    for ch in name_l:
        if i < len(q) and ch == q[i]:
            i += 1
            score += 5
    if i == len(q):
        score += 30
    score += min(len(q), 10)
    return score


def animate_star(btn: QPushButton):
    """Small bounce animation when toggling favourite."""
    rect = btn.geometry()
    anim = QPropertyAnimation(btn, b"geometry")
    anim.setDuration(140)
    anim.setStartValue(rect)
    anim.setKeyValueAt(0.5, rect.adjusted(-2, -2, 2, 2))
    anim.setEndValue(rect)
    anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)


def make_action_widget(app_id, callbacks):
    """Return a QWidget containing small buttons for Launch/Edit/Delete for a table cell."""
    container = QWidget()
    lay = QHBoxLayout(container)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)

    btn_launch = QPushButton("🚀")
    btn_launch.setFixedSize(24, 24)
    btn_launch.clicked.connect(lambda _, aid=app_id: callbacks["launch"](aid))
    lay.addWidget(btn_launch)

    btn_edit = QPushButton("✏️")
    btn_edit.setFixedSize(24, 24)
    btn_edit.clicked.connect(lambda _, aid=app_id: callbacks["edit"](aid))
    lay.addWidget(btn_edit)

    btn_del = QPushButton("✕")
    btn_del.setFixedSize(24, 24)
    btn_del.clicked.connect(lambda _, aid=app_id: callbacks["delete"](aid))
    lay.addWidget(btn_del)

    return container


def make_icon_label(icon_path_or_exe: str | None, size: int = 24) -> QLabel:
    lbl = QLabel()
    lbl.setFixedSize(size, size)
    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

    pixmap = None
    if icon_path_or_exe and os.path.exists(icon_path_or_exe):
        if icon_path_or_exe.lower().endswith((".png", ".ico", ".jpg", ".jpeg", ".bmp")):
            pixmap = QPixmap(icon_path_or_exe)
        else:
            icon = QIcon(icon_path_or_exe)
            pixmap = icon.pixmap(size, size)

    if pixmap and not pixmap.isNull():
        lbl.setPixmap(
            pixmap.scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )
    else:
        lbl.setText("🧩")

    return lbl


def make_fav_button(app: dict, callbacks: dict) -> QPushButton:
    btn = QPushButton("★" if app.get("favorite") else "☆")
    btn.setFixedSize(24, 24)
    btn.clicked.connect(
        lambda _, aid=app["id"], b=btn: (callbacks["toggle_fav"](aid), animate_star(b))
    )
    btn.setStyleSheet("""
        QPushButton {
            background: none;
            border: none;
            font-size: 16px;
            color: #facc15;
        }
        QPushButton:hover {
            color: #fde047;
        }
    """)
    return btn


# ---------------- Card Row Widget (Card Mode) ----------------

class AppRowWidget(QFrame):
    def __init__(self, app_data, callbacks, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.callbacks = callbacks

        self.setObjectName("AppRow")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(12, 8, 12, 8)
        main_layout.setSpacing(10)

        # Favourite button
        self.fav_btn = QPushButton("★" if app_data.get("favorite") else "☆")
        self.fav_btn.setObjectName("FavButton")
        self.fav_btn.setFlat(True)
        self.fav_btn.setFixedWidth(28)
        self.fav_btn.clicked.connect(self.on_toggle_fav)
        self.fav_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(self.fav_btn)

        # Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(28, 28)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setObjectName("AppIcon")
        main_layout.addWidget(self.icon_label)
        self.set_icon_visual()

        # Text block
        text_layout = QVBoxLayout()
        text_layout.setSpacing(0)

        name_label = QLabel(app_data.get("name", "Unnamed App"))
        name_label.setObjectName("AppName")

        category = app_data.get("category") or "General"
        category_label = QLabel(category)
        category_label.setObjectName("AppCategory")

        path_label = QLabel(app_data.get("path", ""))
        path_label.setObjectName("AppPath")
        path_label.setToolTip(app_data.get("path", ""))

        text_layout.addWidget(name_label)
        text_layout.addWidget(category_label)
        text_layout.addWidget(path_label)
        main_layout.addLayout(text_layout)

        spacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        main_layout.addItem(spacer)

        # Buttons
        launch_btn = QPushButton("Launch")
        launch_btn.setObjectName("LaunchButton")
        launch_btn.clicked.connect(self.on_launch)
        launch_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(launch_btn)

        edit_btn = QPushButton("Edit")
        edit_btn.setObjectName("EditButton")
        edit_btn.clicked.connect(self.on_edit)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(edit_btn)

        delete_btn = QPushButton("✕")
        delete_btn.setObjectName("DeleteButton")
        delete_btn.setFixedWidth(28)
        delete_btn.clicked.connect(self.on_delete)
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        main_layout.addWidget(delete_btn)

    def set_icon_visual(self):
        icon_path = self.app_data.get("icon_path")
        pixmap = None
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
        else:
            app_path = self.app_data.get("path")
            if app_path and os.path.exists(app_path):
                icon = QIcon(app_path)
                pixmap = icon.pixmap(28, 28)
        if pixmap and not pixmap.isNull():
            self.icon_label.setPixmap(
                pixmap.scaled(
                    28, 28,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
            self.icon_label.setText("")
        else:
            self.icon_label.setText("🧩")

    def on_launch(self):
        self.callbacks["launch"](self.app_data["id"])

    def on_toggle_fav(self):
        self.callbacks["toggle_fav"](self.app_data["id"])
        animate_star(self.fav_btn)

    def on_edit(self):
        self.callbacks["edit"](self.app_data["id"])

    def on_delete(self):
        self.callbacks["delete"](self.app_data["id"])


# ---------------- Main Window ----------------

class AppLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App Launcher")
        self.setMinimumSize(820, 560)

        default_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(default_icon)

        self.apps: list[dict] = []
        self.next_id: int = 1
        self.filtered_apps: list[dict] = []

        # modes
        self.mode = "card"           # "card" or "compact"
        self.favorite_mode = 0       # 0 = normal, 1 = favs first, 2 = favs only

        # tray
        self.tray_icon: QSystemTrayIcon | None = None
        self.tray_menu: QMenu | None = None

        Path(ICON_DIR).mkdir(exist_ok=True)
        self.load_config()
        self.build_ui()
        self.apply_styles()
        self.setup_shortcuts()
        self.refresh_view()
        self.init_tray_icon()

    # ------- Config -------

    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            self.apps = []
            self.next_id = 1
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self.apps = []
            self.next_id = 1
            return
        if isinstance(data, list):
            self.apps = data
        elif isinstance(data, dict):
            self.apps = data.get("apps", [])
        else:
            self.apps = []
        ids = [app.get("id", 0) for app in self.apps if isinstance(app, dict)]
        self.next_id = max(ids) + 1 if ids else 1

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"apps": self.apps}, f, indent=2)

    # ------- UI -------

    def build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("My App Launcher")
        title.setObjectName("Title")
        subtitle = QLabel("All your apps in one beautiful place ✨")
        subtitle.setObjectName("Subtitle")
        tblock = QVBoxLayout()
        tblock.addWidget(title)
        tblock.addWidget(subtitle)
        header.addLayout(tblock)
        header.addStretch()

        self.toggle_btn = QPushButton("Compact Mode")
        self.toggle_btn.setObjectName("ModeToggle")
        self.toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_mode)
        header.addWidget(self.toggle_btn)

        self.add_btn = QPushButton("+ Add App")
        self.add_btn.setObjectName("AddButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self.add_app)
        header.addWidget(self.add_btn)

        self.main_layout.addLayout(header)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search... Press Enter to launch top match")
        self.search_input.setObjectName("SearchInput")
        self.search_input.textChanged.connect(self.refresh_view)
        self.search_input.returnPressed.connect(self.launch_top_match)
        self.main_layout.addWidget(self.search_input)

        # Suggestion / status label
        self.suggestion_label = QLabel("")
        self.suggestion_label.setObjectName("SuggestionLabel")
        self.suggestion_label.setVisible(False)
        self.main_layout.addWidget(self.suggestion_label)

        # Card list
        self.card_list = QListWidget()
        self.card_list.setObjectName("CardList")
        self.card_list.setSpacing(6)
        self.card_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self.main_layout.addWidget(self.card_list)

        self.card_opacity = QGraphicsOpacityEffect(self.card_list)
        self.card_list.setGraphicsEffect(self.card_opacity)

        # Compact table
        self.table = QTableWidget()
        self.table.setObjectName("CompactTable")
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["", "", "Name", "Category", "Path", "Actions"])
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.resizeSection(0, 32)  # fav
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header_view.resizeSection(1, 36)  # icon
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header_view.resizeSection(5, 110)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.SingleSelection)
        self.table.setEditTriggers(self.table.EditTrigger.NoEditTriggers)
        self.main_layout.addWidget(self.table)
        self.table.hide()  # start in card mode

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #050814;
                color: #f5f5f5;
                font-family: "Segoe UI", "Roboto", sans-serif;
                font-size: 13px;
            }

            #Title {
                font-size: 22px;
                font-weight: 700;
            }
            #Subtitle {
                font-size: 11px;
                color: #9ca3af;
            }

            #ModeToggle {
                padding: 6px 12px;
                border-radius: 8px;
                background-color: #0b1224;
                border: 1px solid #1f2937;
            }

            #AddButton {
                padding: 8px 14px;
                border-radius: 10px;
                border: none;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #6366f1,
                    stop:1 #ec4899
                );
                color: white;
                font-weight: 600;
            }

            #SearchInput {
                padding: 10px;
                border-radius: 10px;
                border: 1px solid #1f2937;
                background-color: #020617;
            }

            #SuggestionLabel {
                font-size: 11px;
                color: #9ca3af;
                padding-left: 4px;
                padding-top: 2px;
            }

            #CardList {
                border: none;
                background: transparent;
            }

            #AppRow {
                background-color: #020617;
                border-radius: 12px;
                border: 1px solid #111827;
            }
            #AppRow:hover {
                border: 1px solid #4b5563;
                background-color: #0b1220;
            }

            #AppIcon {
                background-color: #111827;
                border-radius: 8px;
            }
            #AppName { font-size: 14px; font-weight: 600; }
            #AppCategory { font-size: 11px; color: #9ca3af; }
            #AppPath { font-size: 10px; color: #6b7280; }

            #FavButton {
                border: none;
                background: none;
                font-size: 18px;
                color: #facc15;
            }

            #LaunchButton, #EditButton, #DeleteButton {
                padding: 6px 10px;
                border-radius: 999px;
                border: 1px solid #374151;
                background-color: #020617;
            }

            #LaunchButton {
                font-weight: 600;
            }

            #CompactTable {
                background: transparent;
                border: none;
            }
            QHeaderView::section {
                background: #071027;
                padding: 6px;
                border: 1px solid #111827;
                font-weight: 600;
            }
        """)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.WindowText, pal.color(QPalette.ColorRole.BrightText))
        self.setPalette(pal)

    # ------- Shortcuts -------

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.focus_search)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_app)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=QApplication.instance().quit)
        QShortcut(QKeySequence("Ctrl+Up"), self, activated=lambda: self.move_selection(-1))
        QShortcut(QKeySequence("Ctrl+Down"), self, activated=lambda: self.move_selection(1))
        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self.launch_selected)
        QShortcut(QKeySequence("F"), self, activated=self.cycle_favorite_mode)

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

    def move_selection(self, delta: int):
        if self.mode == "card":
            count = self.card_list.count()
            if count == 0:
                return
            cur = self.card_list.currentRow()
            if cur < 0:
                new = 0 if delta > 0 else count - 1
            else:
                new = max(0, min(count - 1, cur + delta))
            self.card_list.setCurrentRow(new)
        else:
            count = self.table.rowCount()
            if count == 0:
                return
            cur = self.table.currentRow()
            if cur < 0:
                new = 0 if delta > 0 else count - 1
            else:
                new = max(0, min(count - 1, cur + delta))
            self.table.selectRow(new)

    def launch_selected(self):
        if self.mode == "card":
            row = self.card_list.currentRow()
            if row < 0:
                return
            item = self.card_list.item(row)
            widget = self.card_list.itemWidget(item)
            if widget:
                widget.on_launch()
        else:
            row = self.table.currentRow()
            if row < 0 or row >= len(self.filtered_apps):
                return
            app = self.filtered_apps[row]
            self.launch_app(app["id"])

    def cycle_favorite_mode(self):
        # 0 -> 1 -> 2 -> 0
        self.favorite_mode = (self.favorite_mode + 1) % 3
        if self.favorite_mode == 0:
            self.suggestion_label.setText("Mode: Normal")
        elif self.favorite_mode == 1:
            self.suggestion_label.setText("Mode: Favorites First")
        else:
            self.suggestion_label.setText("Mode: Favorites Only")
        self.suggestion_label.setVisible(True)
        self.refresh_view()

    # ------- Tray -------

    def init_tray_icon(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        icon = self.windowIcon()
        self.tray_icon = QSystemTrayIcon(icon, self)
        self.tray_menu = QMenu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_click)
        self.tray_icon.show()
        self.update_tray_menu()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isHidden() or self.isMinimized():
                self.showNormal()
                self.raise_()
                self.activateWindow()
            else:
                self.hide()

    def update_tray_menu(self):
        if not self.tray_menu:
            return
        self.tray_menu.clear()
        show_act = QAction("Show Launcher", self)
        show_act.triggered.connect(self.showNormal)
        self.tray_menu.addAction(show_act)
        favs = [a for a in self.apps if a.get("favorite")]
        if favs:
            self.tray_menu.addSeparator()
            for app in favs[:10]:
                act = QAction(f"Launch: {app['name']}", self)
                act.triggered.connect(lambda _, aid=app["id"]: self.launch_app(aid))
                self.tray_menu.addAction(act)
        self.tray_menu.addSeparator()
        quit_act = QAction("Quit", self)
        quit_act.triggered.connect(QApplication.instance().quit)
        self.tray_menu.addAction(quit_act)

    def closeEvent(self, event):
        if self.tray_icon:
            self.hide()
            event.ignore()
        else:
            event.accept()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.hide()
        super().changeEvent(event)

    # ------- Mode & Refresh -------

    def toggle_mode(self):
        if self.mode == "card":
            self.mode = "compact"
            self.toggle_btn.setText("Card Mode")
            self.card_list.hide()
            self.table.show()
            self.table.setFocus()
        else:
            self.mode = "card"
            self.toggle_btn.setText("Compact Mode")
            self.table.hide()
            self.card_list.show()
        self.refresh_view()

    def refresh_view(self):
        if self.mode == "card":
            self.refresh_card_list()
        else:
            self.refresh_table()

    def _ordered_apps(self, query: str) -> list[dict]:
        favs = [a for a in self.apps if a.get("favorite")]
        non_favs = [a for a in self.apps if not a.get("favorite")]

        # favorite_mode
        if self.favorite_mode == 2:  # favorites only
            base = favs
        else:
            base = favs + non_favs  # normal & favs-first same ordering

        if not query:
            return base

        # fuzzy filter
        scored = []
        for app in base:
            text = f"{app.get('name','')} {app.get('category','')}"
            score = fuzzy_score(text, query)
            if score > 0:
                scored.append((score, app))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored]

    def refresh_card_list(self):
        query = self.search_input.text().strip().lower()
        apps = self._ordered_apps(query)
        self.filtered_apps = apps

        self.card_list.clear()
        for app in apps:
            item = QListWidgetItem(self.card_list)
            item.setSizeHint(QSize(0, 70))
            callbacks = {
                "launch": self.launch_app,
                "toggle_fav": self.toggle_favorite,
                "edit": self.edit_app,
                "delete": self.delete_app
            }
            row_widget = AppRowWidget(app, callbacks)

            # highlight favourites softly
            if app.get("favorite"):
                row_widget.setStyleSheet(
                    "QFrame#AppRow { border: 1px solid #facc15; background-color: #111827; }"
                )

            self.card_list.setItemWidget(item, row_widget)

        # suggestion / mode display
        if apps and query:
            top = apps[0]
            self.suggestion_label.setText(
                f"Top match: {top.get('name','App')} · {top.get('category','General')} (Enter to launch)"
            )
            self.suggestion_label.setVisible(True)

        # fade animation
        self.card_opacity.setOpacity(0.0)
        anim = QPropertyAnimation(self.card_opacity, b"opacity", self)
        anim.setDuration(150)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

        self.update_tray_menu()

    def refresh_table(self):
        query = self.search_input.text().strip().lower()
        apps = self._ordered_apps(query)
        self.filtered_apps = apps
        self.table.setRowCount(len(apps))

        callbacks = {
            "launch": self.launch_app,
            "edit": self.edit_app,
            "delete": self.delete_app,
            "toggle_fav": self.toggle_favorite,
        }

        for r, app in enumerate(apps):
            # favourite star widget
            fav_btn = make_fav_button(app, callbacks)
            self.table.setCellWidget(r, 0, fav_btn)

            # icon
            icon_widget = make_icon_label(app.get("icon_path") or app.get("path"), size=24)
            self.table.setCellWidget(r, 1, icon_widget)

            # name
            name_item = QTableWidgetItem(app.get("name", ""))
            self.table.setItem(r, 2, name_item)

            # category
            cat_item = QTableWidgetItem(app.get("category", ""))
            self.table.setItem(r, 3, cat_item)

            # path
            path_item = QTableWidgetItem(app.get("path", ""))
            self.table.setItem(r, 4, path_item)

            # actions
            actions_widget = make_action_widget(app.get("id"), callbacks)
            self.table.setCellWidget(r, 5, actions_widget)

            # favourite highlighting
            if app.get("favorite"):
                for c in (2, 3, 4):
                    it = self.table.item(r, c)
                    if it:
                        it.setBackground(QColor("#1a1a06"))

        if apps and query:
            top = apps[0]
            self.suggestion_label.setText(
                f"Top match: {top.get('name','App')} · {top.get('category','General')} (Enter to launch)"
            )
            self.suggestion_label.setVisible(True)

        if self.table.rowCount() > 0:
            self.table.selectRow(0)

        self.update_tray_menu()

    # ------- CRUD -------

    def add_app(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Application",
            str(Path.home()),
            "Executables (*.exe *.bat *.cmd *.sh *.AppImage);;All Files (*)"
        )
        if not file_path:
            return

        default_name = os.path.splitext(os.path.basename(file_path))[0]
        name, ok = self.simple_input("App Name", "Enter name:", default_name)
        if not ok or not name.strip():
            return

        category, ok = self.simple_input("Category", "Enter category:", "General")
        if not ok:
            return

        app = {
            "id": self.next_id,
            "name": name.strip(),
            "path": file_path,
            "category": category.strip() or "General",
            "favorite": False,
        }

        # icon extraction
        try:
            icon = QIcon(file_path)
            pix = icon.pixmap(64, 64)
            if pix and not pix.isNull():
                Path(ICON_DIR).mkdir(exist_ok=True)
                dst = os.path.join(ICON_DIR, f"{app['id']}.png")
                pix.save(dst, "PNG")
                app["icon_path"] = dst
        except Exception:
            pass

        self.next_id += 1
        self.apps.append(app)
        self.save_config()
        self.refresh_view()

    def edit_app(self, app_id):
        app = self.get_app(app_id)
        if not app:
            return

        name, ok = self.simple_input("Edit Name", "Name:", app.get("name", ""))
        if ok and name.strip():
            app["name"] = name.strip()

        category, ok = self.simple_input("Edit Category", "Category:", app.get("category", "General"))
        if ok:
            app["category"] = category.strip() or "General"

        self.save_config()
        self.refresh_view()

    def delete_app(self, app_id):
        app = self.get_app(app_id)
        if not app:
            return
        reply = QMessageBox.question(
            self,
            "Delete App",
            f"Remove \"{app.get('name','App')}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            icon_path = app.get("icon_path")
            if icon_path and os.path.exists(icon_path):
                try:
                    os.remove(icon_path)
                except Exception:
                    pass
            self.apps = [a for a in self.apps if a["id"] != app_id]
            self.save_config()
            self.refresh_view()

    def toggle_favorite(self, app_id):
        app = self.get_app(app_id)
        if not app:
            return
        app["favorite"] = not app.get("favorite", False)
        self.save_config()
        self.refresh_view()

    def launch_app(self, app_id):
        app = self.get_app(app_id)
        if not app:
            return
        try:
            open_file_cross_platform(app["path"])
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def get_app(self, app_id):
        for app in self.apps:
            if app.get("id") == app_id:
                return app
        return None

    # ------- Utils -------

    def simple_input(self, title, label, default=""):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        layout = QVBoxLayout(dialog)
        lbl = QLabel(label)
        line = QLineEdit(default)
        layout.addWidget(lbl)
        layout.addWidget(line)
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            return line.text(), True
        return default, False

    def launch_top_match(self):
        if not self.filtered_apps:
            return
        top = self.filtered_apps[0]
        self.launch_app(top["id"])

    # responsive resize for compact mode
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.mode == "compact":
            total = max(400, self.table.viewport().width())
            name_w = int(total * 0.25)
            cat_w = int(total * 0.15)
            path_w = int(total * 0.45)
            self.table.setColumnWidth(0, 32)
            self.table.setColumnWidth(1, 36)
            self.table.setColumnWidth(2, name_w)
            self.table.setColumnWidth(3, cat_w)
            self.table.setColumnWidth(4, path_w)
            self.table.setColumnWidth(5, 110)


# ---------- Entry ----------

def main():
    app = QApplication(sys.argv)
    window = AppLauncher()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
