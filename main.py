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
    QDialogButtonBox, QSystemTrayIcon, QMenu, QStyle,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QLayout,
    QCheckBox, QAbstractButton
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QAction, QShortcut, QKeySequence, QPalette, QColor,
    QPainter, QBrush, QPen
)
from PyQt6.QtCore import (
    Qt, QSize, QEvent, QPropertyAnimation, QPoint, QRect, QTimer,
    QEasingCurve
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect

CONFIG_FILE = "apps.json"
ICON_DIR = "icons"


# ---------------- Flow Layout ----------------

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        spacing = self.spacing()

        for item in self.itemList:
            wid = item.widget()
            spaceX = spacing + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Horizontal)
            spaceY = spacing + wid.style().layoutSpacing(QSizePolicy.ControlType.PushButton, QSizePolicy.ControlType.PushButton, Qt.Orientation.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()

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





# ---------------- Card Row Widget (Card Mode) ----------------

# ---------------- App Card Widget (Tile Mode) ----------------

class AppCardWidget(QFrame):
    def __init__(self, app_data, callbacks, parent=None):
        super().__init__(parent)
        self.app_data = app_data
        self.callbacks = callbacks

        self.setObjectName("AppCard")
        self.setFixedSize(160, 200)  # Taller to fit name
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(f"{app_data.get('category', 'General')}")
        
        # Context Menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 16)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Top container for Fav button
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addStretch()
        
        self.fav_btn = QPushButton("★" if app_data.get("favorite") else "☆")
        self.fav_btn.setObjectName("FavButtonCard")
        self.fav_btn.setFixedSize(28, 28)
        self.fav_btn.clicked.connect(self.on_toggle_fav)
        self.fav_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        top_layout.addWidget(self.fav_btn)
        
        layout.addLayout(top_layout)

        # Icon container
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(80, 80)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_label.setObjectName("AppIconCard")
        # Default style for placeholder
        self.icon_label.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
        """)
        layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.set_icon_visual()
        
        # Name
        name_label = QLabel(app_data.get("name", "Unnamed"))
        name_label.setObjectName("AppNameCard")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        name_label.setStyleSheet("font-size: 14px; font-weight: 600; color: #e4e4e7; margin-top: 4px;")
        layout.addWidget(name_label)
        
        layout.addStretch()

    def set_icon_visual(self):
        icon_path = self.app_data.get("icon_path")
        pixmap = None
        if icon_path and os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
        else:
            app_path = self.app_data.get("path")
            if app_path and os.path.exists(app_path):
                icon = QIcon(app_path)
                pixmap = icon.pixmap(128, 128)
        
        if pixmap and not pixmap.isNull():
            self.icon_label.setPixmap(
                pixmap.scaled(
                    96, 96,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            self.icon_label.setText("⚡")
            self.icon_label.setStyleSheet("""
                QLabel {
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:1,
                        stop:0 rgba(139, 92, 246, 0.15),
                        stop:1 rgba(99, 102, 241, 0.15)
                    );
                    color: #a78bfa;
                    border-radius: 24px;
                    border: 1px solid rgba(139, 92, 246, 0.3);
                    font-size: 48px;
                }
            """)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # Check if we clicked on buttons
            child = self.childAt(event.pos())
            if not isinstance(child, QPushButton):
                self.on_launch()
        super().mousePressEvent(event)

    def show_context_menu(self, pos):
        menu = QMenu(self)
        
        launch_act = QAction("🚀 Launch", self)
        launch_act.triggered.connect(self.on_launch)
        menu.addAction(launch_act)
        
        menu.addSeparator()
        
        fav_text = "Remove from Favorites" if self.app_data.get("favorite") else "Add to Favorites"
        fav_act = QAction(f"⭐️ {fav_text}", self)
        fav_act.triggered.connect(self.on_toggle_fav)
        menu.addAction(fav_act)
        
        edit_act = QAction("✏️ Edit", self)
        edit_act.triggered.connect(self.on_edit)
        menu.addAction(edit_act)
        
        loc_act = QAction("📂 Open File Location", self)
        loc_act.triggered.connect(self.on_open_location)
        menu.addAction(loc_act)
        
        menu.addSeparator()
        
        del_act = QAction("🗑️ Delete", self)
        del_act.triggered.connect(self.on_delete)
        menu.addAction(del_act)
        
        menu.exec(self.mapToGlobal(pos))

    def on_launch(self):
        self.callbacks["launch"](self.app_data["id"])

    def on_toggle_fav(self):
        self.callbacks["toggle_fav"](self.app_data["id"])
        animate_star(self.fav_btn)

    def on_edit(self):
        self.callbacks["edit"](self.app_data["id"])

    def on_delete(self):
        self.callbacks["delete"](self.app_data["id"])
        
    def on_open_location(self):
        path = self.app_data.get("path")
        if path and os.path.exists(path):
            folder = os.path.dirname(path)
            open_file_cross_platform(folder)



class EditAppDialog(QDialog):
    def __init__(self, parent, app_data):
        super().__init__(parent)
        self.setWindowTitle("Edit App")
        self.setMinimumWidth(400)
        self.app_data = app_data
        self.result_data = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Name
        layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(app_data.get("name", ""))
        layout.addWidget(self.name_edit)

        # Category
        layout.addWidget(QLabel("Category:"))
        self.cat_edit = QLineEdit(app_data.get("category", ""))
        layout.addWidget(self.cat_edit)

        # Path
        layout.addWidget(QLabel("Path:"))
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit(app_data.get("path", ""))
        path_layout.addWidget(self.path_edit)
        browse_path_btn = QPushButton("Browse...")
        browse_path_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(browse_path_btn)
        layout.addLayout(path_layout)

        # Icon
        layout.addWidget(QLabel("Icon Path (Optional):"))
        icon_layout = QHBoxLayout()
        self.icon_edit = QLineEdit(app_data.get("icon_path", ""))
        icon_layout.addWidget(self.icon_edit)
        browse_icon_btn = QPushButton("Browse...")
        browse_icon_btn.clicked.connect(self.browse_icon)
        icon_layout.addWidget(browse_icon_btn)
        layout.addLayout(icon_layout)

        # Buttons
        btn_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        btn_box.accepted.connect(self.validate_and_accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def browse_path(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Application", str(Path.home()),
            "Executables (*.exe *.bat *.cmd *.sh *.AppImage);;All Files (*)"
        )
        if file_path:
            self.path_edit.setText(file_path)

    def browse_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Icon", str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.ico *.bmp);;All Files (*)"
        )
        if file_path:
            self.icon_edit.setText(file_path)

    def validate_and_accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Validation Error", "Name cannot be empty.")
            return
        
        self.result_data = {
            "name": name,
            "category": self.cat_edit.text().strip() or "General",
            "path": self.path_edit.text().strip(),
            "icon_path": self.icon_edit.text().strip()
        }
        self.accept()


# ---------------- Main Window ----------------

class Toggle(QCheckBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        
        # Track
        if self.isChecked():
            p.setBrush(QColor("#8b5cf6"))
            p.setPen(Qt.PenStyle.NoPen)
        else:
            p.setBrush(QColor("#3f3f46"))
            p.setPen(Qt.PenStyle.NoPen)
            
        p.drawRoundedRect(0, 0, rect.width(), rect.height(), 12, 12)
        
        # Knob
        p.setBrush(QColor("#ffffff"))
        if self.isChecked():
            p.drawEllipse(22, 2, 20, 20)
        else:
            p.drawEllipse(2, 2, 20, 20)
        p.end()

class SettingsDialog(QDialog):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self.settings = settings
        self.result_settings = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(24)
        layout.setContentsMargins(32, 32, 32, 32)

        # Header
        header = QHBoxLayout()
        title = QLabel("Settings")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #ffffff;")
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # General Section
        layout.addWidget(self.create_section_header("General"))
        
        # Minimize to Tray
        self.min_tray_toggle = Toggle()
        self.min_tray_toggle.setChecked(settings.get("minimize_to_tray", True))
        layout.addLayout(self.create_option_row("Minimize to System Tray", "Keep app running in background when closed", self.min_tray_toggle))

        # Start Minimized
        self.start_min_toggle = Toggle()
        self.start_min_toggle.setChecked(settings.get("start_minimized", False))
        layout.addLayout(self.create_option_row("Start Minimized", "Launch application silently in the tray", self.start_min_toggle))

        layout.addStretch()

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a1a1aa;
                padding: 10px 20px;
                font-weight: 600;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                color: #ffffff;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #000000;
                padding: 10px 24px;
                border-radius: 10px;
                font-weight: 700;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background: #e4e4e7;
            }
        """)
        save_btn.clicked.connect(self.save_and_accept)
        btn_box.addWidget(save_btn)
        
        layout.addLayout(btn_box)
        
        self.setStyleSheet("QDialog { background: #18181b; }")

    def create_section_header(self, text):
        label = QLabel(text)
        label.setStyleSheet("""
            color: #8b5cf6;
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 8px;
        """)
        return label

    def create_option_row(self, title, subtitle, widget):
        row = QHBoxLayout()
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        
        t_label = QLabel(title)
        t_label.setStyleSheet("color: #e4e4e7; font-size: 15px; font-weight: 600;")
        text_layout.addWidget(t_label)
        
        s_label = QLabel(subtitle)
        s_label.setStyleSheet("color: #a1a1aa; font-size: 13px;")
        text_layout.addWidget(s_label)
        
        row.addLayout(text_layout)
        row.addStretch()
        row.addWidget(widget)
        return row

    def save_and_accept(self):
        self.result_settings = {
            "minimize_to_tray": self.min_tray_toggle.isChecked(),
            "start_minimized": self.start_min_toggle.isChecked()
        }
        self.accept()


# ---------------- Main Window ----------------

class AppLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App Launcher")
        self.setMinimumSize(900, 600)
        self.setAcceptDrops(True)  # Enable Drag & Drop

        default_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.setWindowIcon(default_icon)

        self.apps: list[dict] = []
        self.next_id: int = 1
        self.filtered_apps: list[dict] = []
        self.first_run: bool = True
        self.settings: dict = {
            "minimize_to_tray": True,
            "start_minimized": False
        }

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
            self.first_run = True
            self.settings = {"minimize_to_tray": True, "start_minimized": False}
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            self.apps = []
            self.next_id = 1
            self.first_run = True
            self.settings = {"minimize_to_tray": True, "start_minimized": False}
            return
            
        if isinstance(data, dict):
            self.apps = data.get("apps", [])
            self.first_run = data.get("first_run", True)
            self.settings = data.get("settings", {"minimize_to_tray": True, "start_minimized": False})
        else:
            # Migration from old list format
            if isinstance(data, list):
                self.apps = data
            else:
                self.apps = []
            self.first_run = True
            self.settings = {"minimize_to_tray": True, "start_minimized": False}
            
        ids = [app.get("id", 0) for app in self.apps if isinstance(app, dict)]
        self.next_id = max(ids) + 1 if ids else 1

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "apps": self.apps, 
                "first_run": self.first_run,
                "settings": self.settings
            }, f, indent=2)

    # ------- UI -------

    def build_ui(self):
        # Main container with horizontal layout
        container = QHBoxLayout(self)
        container.setContentsMargins(0, 0, 0, 0)
        container.setSpacing(0)
        
        # === SIDEBAR ===
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(32, 48, 32, 32)
        sidebar_layout.setSpacing(24)
        
        # Logo/Title
        logo_container = QHBoxLayout()
        logo_container.setSpacing(12)
        logo = QLabel("🚀")
        logo.setStyleSheet("font-size: 32px;")
        logo_container.addWidget(logo)
        
        app_title = QLabel("Launcher")
        app_title.setObjectName("SidebarTitle")
        logo_container.addWidget(app_title)
        logo_container.addStretch()
        
        sidebar_layout.addLayout(logo_container)
        sidebar_layout.addSpacing(24)
        
        # Search in sidebar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search apps...")
        self.search_input.setObjectName("SidebarSearch")
        self.search_input.setToolTip("Ctrl+P")
        self.search_input.textChanged.connect(self.refresh_view)
        self.search_input.returnPressed.connect(self.launch_top_match)
        sidebar_layout.addWidget(self.search_input)
        
        # Category filters
        categories_label = QLabel("LIBRARY")
        categories_label.setObjectName("SidebarSectionTitle")
        sidebar_layout.addWidget(categories_label)
        
        # Add category buttons (we'll populate dynamically)
        self.category_buttons_layout = QVBoxLayout()
        self.category_buttons_layout.setSpacing(4)
        sidebar_layout.addLayout(self.category_buttons_layout)
        
        sidebar_layout.addSpacing(24)
        
        # System Section
        system_label = QLabel("SYSTEM")
        system_label.setObjectName("SidebarSectionTitle")
        sidebar_layout.addWidget(system_label)
        
        # System Actions
        self.system_buttons_layout = QVBoxLayout()
        self.system_buttons_layout.setSpacing(4)
        sidebar_layout.addLayout(self.system_buttons_layout)

        self.add_btn = QPushButton("Add Application")
        self.add_btn.setObjectName("SidebarButton")
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileIcon)))
        self.add_btn.clicked.connect(self.add_app)
        self.system_buttons_layout.addWidget(self.add_btn)
        
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("SidebarButton")
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogDetailedView)))
        settings_btn.clicked.connect(self.show_settings)
        self.system_buttons_layout.addWidget(settings_btn)
        
        help_btn = QPushButton("Shortcuts")
        help_btn.setObjectName("SidebarButton")
        help_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        help_btn.clicked.connect(self.show_keyboard_shortcuts)
        self.system_buttons_layout.addWidget(help_btn)
        
        sidebar_layout.addStretch()
        
        container.addWidget(self.sidebar)
        
        # === MAIN CONTENT AREA ===
        main_area = QWidget()
        main_area.setObjectName("MainArea")
        main_layout = QVBoxLayout(main_area)
        main_layout.setContentsMargins(48, 48, 48, 48)
        main_layout.setSpacing(32)
        
        # Top bar
        top_bar = QHBoxLayout()
        
        # Menu Button (Hamburger)
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setObjectName("MenuButton")
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.setFixedSize(40, 40)
        self.menu_btn.clicked.connect(self.toggle_sidebar)
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a1a1aa;
                font-size: 20px;
                border: 1px solid #27272a;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: #27272a;
                color: #ffffff;
            }
        """)
        top_bar.addWidget(self.menu_btn)
        
        # Page title
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        page_title = QLabel("Dashboard")
        page_title.setObjectName("PageTitle")
        title_layout.addWidget(page_title)
        
        subtitle = QLabel("Manage and launch your favorite applications")
        subtitle.setObjectName("PageSubtitle")
        title_layout.addWidget(subtitle)
        
        top_bar.addLayout(title_layout)
        top_bar.addStretch()
        
        # Suggestion label
        self.suggestion_label = QLabel("")
        self.suggestion_label.setObjectName("SuggestionLabel")
        self.suggestion_label.setVisible(False)
        top_bar.addWidget(self.suggestion_label)
        
        main_layout.addLayout(top_bar)
        
        # Content area with empty state
        self.content_area = QVBoxLayout()
        main_layout.addLayout(self.content_area)
        
        # Empty State
        self.empty_state = QLabel("No apps found.\nDrag & drop files here or click 'Add Application'")
        self.empty_state.setObjectName("EmptyState")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.hide()
        self.content_area.addWidget(self.empty_state)
        
        # Scroll Area for Grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("ScrollArea")
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("ScrollContent")
        self.flow_layout = FlowLayout(self.scroll_content, margin=0, spacing=24)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.content_area.addWidget(self.scroll_area)
        
        # Toast notification
        self.toast_label = QLabel()
        self.toast_label.setObjectName("Toast")
        self.toast_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.toast_label.setFixedHeight(48)
        self.toast_label.hide()
        
        # Add to main layout
        main_layout.addWidget(self.toast_label, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom)
        
        container.addWidget(main_area)
        
        # Show welcome if first run
        if self.first_run:
            QTimer.singleShot(500, self.show_welcome_message)

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background: #09090b;
                color: #e4e4e7;
                font-family: "Segoe UI", "Inter", sans-serif;
                font-size: 14px;
            }
            
            /* ========== SIDEBAR ========== */
            #Sidebar {
                background: #18181b;
                border-right: 1px solid #27272a;
            }
            
            #SidebarTitle {
                font-size: 20px;
                font-weight: 700;
                color: #ffffff;
                letter-spacing: -0.5px;
            }
            
            #SidebarSectionTitle {
                font-size: 12px;
                font-weight: 600;
                color: #71717a;
                letter-spacing: 1px;
                padding: 8px 4px;
                margin-top: 12px;
            }
            
            #SidebarSearch {
                padding: 12px 16px;
                border-radius: 12px;
                border: 1px solid #27272a;
                background: #27272a;
                color: #ffffff;
                font-size: 14px;
            }
            #SidebarSearch:focus {
                border: 1px solid #8b5cf6;
                background: #27272a;
            }
            
            #SidebarButton {
                text-align: left;
                padding: 10px 16px;
                border: none;
                background: transparent;
                border-radius: 8px;
                color: #a1a1aa;
                font-weight: 500;
                font-size: 14px;
                min-height: 20px;
                qproperty-iconSize: 18px 18px;
                border-left: 3px solid transparent;
            }
            #SidebarButton:hover {
                background: #27272a;
                color: #ffffff;
                padding-left: 20px; /* Slide effect */
            }
            #SidebarButton[active="true"] {
                background: #27272a;
                color: #ffffff;
                font-weight: 600;
                border-left: 3px solid #8b5cf6;
                padding-left: 13px; /* Compensate for border to keep text aligned */
            }
            
            /* ========== MAIN AREA ========== */
            #MainArea {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #09090b,
                    stop:1 #101012
                );
            }
            
            #PageTitle {
                font-size: 36px;
                font-weight: 800;
                color: #ffffff;
                letter-spacing: -1px;
            }
            
            #PageSubtitle {
                font-size: 16px;
                color: #a1a1aa;
                font-weight: 400;
            }
            
            #SuggestionLabel {
                font-size: 13px;
                color: #a78bfa;
                padding: 8px 16px;
                background: rgba(139, 92, 246, 0.1);
                border-radius: 20px;
                border: 1px solid rgba(139, 92, 246, 0.2);
                font-weight: 600;
            }
            
            #ScrollArea, #ScrollContent {
                background: transparent;
                border: none;
            }
            
            /* ========== APP CARDS ========== */
            #AppCard {
                background: #18181b;
                border-radius: 24px;
                border: 1px solid #27272a;
            }
            #AppCard:hover {
                background: #27272a;
                border: 1px solid #3f3f46;
                margin-top: -4px; /* Lift effect */
            }
            
            #AppNameCard {
                font-size: 16px;
                font-weight: 600;
                color: #f4f4f5;
                margin-top: 4px;
            }
            
            #AppCategoryCard {
                font-size: 12px;
                color: #71717a;
                font-weight: 500;
            }
            
            #FavButtonCard {
                border: none;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 18px;
                font-size: 18px;
                color: #71717a;
            }
            #FavButtonCard:hover {
                background: rgba(251, 191, 36, 0.15);
                color: #fbbf24;
            }
            
            #EmptyState {
                font-size: 18px;
                color: #52525b;
                font-weight: 500;
            }
            
            #Toast {
                background: #18181b;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 12px 24px;
                border-radius: 24px;
                border: 1px solid #3f3f46;
            }
            
            /* ========== MENUS ========== */
            QMenu {
                background: #18181b;
                border: 1px solid #27272a;
                border-radius: 12px;
                padding: 6px;
            }
            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 6px;
                color: #e4e4e7;
            }
            QMenu::item:selected {
                background: #27272a;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background: #27272a;
                margin: 4px 8px;
            }
            
            /* ========== SCROLLBAR ========== */
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #3f3f46;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #52525b;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.WindowText, QColor("#e4e4e7"))
        self.setPalette(pal)

    # ------- Shortcuts -------

    def toggle_favorite_mode(self):
        # Cycle: 0 -> 2 -> 0 (Toggle between Normal and Favs Only for sidebar button)
        if self.favorite_mode == 2:
            self.favorite_mode = 0
            self.show_toast("Showing all apps")
        else:
            self.favorite_mode = 2
            self.show_toast("Showing favorites only")
        self.refresh_view()

    def set_favorite_mode(self, mode):
        self.favorite_mode = mode
        self.refresh_view()

    def show_settings(self):
        dialog = SettingsDialog(self, self.settings)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.result_settings
            self.save_config()
            self.show_toast("Settings saved")

    def setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+P"), self, activated=self.focus_search)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.add_app)
        QShortcut(QKeySequence("Ctrl+Q"), self, activated=QApplication.instance().quit)
        QShortcut(QKeySequence("F"), self, activated=self.cycle_favorite_mode)
        QShortcut(QKeySequence("F1"), self, activated=self.show_keyboard_shortcuts)

    def focus_search(self):
        self.search_input.setFocus()
        self.search_input.selectAll()

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
    
    # ------- User Assistance -------
    
    def show_keyboard_shortcuts(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Keyboard Shortcuts")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(32, 32, 32, 32)
        
        title = QLabel("Keyboard Shortcuts")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #ffffff; margin-bottom: 8px;")
        layout.addWidget(title)
        
        shortcuts = [
            ("Ctrl+P", "Focus search bar"),
            ("Ctrl+N", "Add new app"),
            ("Ctrl+Q", "Quit application"),
            ("F", "Cycle favorite mode"),
            ("F1", "Show this help dialog"),
            ("Enter", "Launch top search result"),
        ]
        
        for key, desc in shortcuts:
            row = QHBoxLayout()
            row.setSpacing(16)
            
            key_label = QLabel(key)
            key_label.setStyleSheet("""
                background: #27272a;
                padding: 8px 16px;
                border-radius: 8px;
                font-weight: 700;
                color: #a78bfa;
                border: 1px solid #3f3f46;
                min-width: 80px;
            """)
            key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            row.addWidget(key_label)
            
            desc_label = QLabel(desc)
            desc_label.setStyleSheet("color: #d4d4d8; font-size: 14px; font-weight: 500;")
            row.addWidget(desc_label, 1)
            
            layout.addLayout(row)
        
        layout.addSpacing(16)
        
        close_btn = QPushButton("Got it")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #000000;
                padding: 12px 24px;
                border-radius: 10px;
                font-weight: 700;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background: #e4e4e7;
            }
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setStyleSheet("""
            QDialog {
                background: #18181b;
            }
            QLabel {
                color: #e4e4e7;
            }
        """)
        dialog.exec()
    
    def show_welcome_message(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Welcome!")
        dialog.setMinimumWidth(550)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        
        title = QLabel("👋 Welcome to App Launcher!")
        title.setStyleSheet("font-size: 24px; font-weight: 800; color: #a78bfa; margin-bottom: 8px;")
        layout.addWidget(title)
        
        intro = QLabel("Your beautiful, organized app management center")
        intro.setStyleSheet("font-size: 14px; color: #94a3b8; margin-bottom: 16px;")
        layout.addWidget(intro)
        
        tips_title = QLabel("✨ Quick Tips:")
        tips_title.setStyleSheet("font-size: 16px; font-weight: 700; color: #f8fafc; margin-top: 8px;")
        layout.addWidget(tips_title)
        
        tips = [
            "• Drag & drop .exe files to add them instantly",
            "• Right-click app cards for quick actions",
            "• Press F to cycle through favorite modes",
            "• Press F1 anytime to see all keyboard shortcuts",
            "• Click the ⭐ to mark apps as favorites",
        ]
        
        for tip in tips:
            tip_label = QLabel(tip)
            tip_label.setStyleSheet("color: #cbd5e1; font-size: 13px; padding: 4px 0;")
            layout.addWidget(tip_label)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        got_it_btn = QPushButton("Let's Go! 🚀")
        got_it_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #6366f1, stop:1 #8b5cf6);
                color: white;
                padding: 12px 32px;
                border-radius: 10px;
                font-weight: 700;
                font-size: 14px;
                margin-top: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #7c3aed, stop:1 #a855f7);
            }
        """)
        got_it_btn.clicked.connect(lambda: (
            setattr(self, 'first_run', False),
            self.save_config(),
            dialog.accept()
        ))
        btn_layout.addWidget(got_it_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        dialog.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
            }
            QLabel {
                color: #f8fafc;
            }
        """)
        dialog.exec()
    
    def show_toast(self, message, duration=2000):
        self.toast_label.setText(message)
        self.toast_label.show()
        QTimer.singleShot(duration, self.toast_label.hide)

    # ------- Drag & Drop -------

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            if os.path.isfile(f):
                self.add_app_from_path(f)
        event.acceptProposedAction()

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
        if self.tray_icon and self.settings.get("minimize_to_tray", True):
            self.hide()
            self.show_toast("Minimized to tray")
            event.ignore()
        else:
            event.accept()

    def resizeEvent(self, event):
        # Auto-collapse sidebar on small screens
        if self.width() < 900:
            if self.sidebar.width() > 0:
                self.toggle_sidebar(force_collapse=True)
        else:
            if self.sidebar.width() == 0:
                self.toggle_sidebar(force_expand=True)
        super().resizeEvent(event)

    def toggle_sidebar(self, checked=False, force_collapse=False, force_expand=False):
        width = self.sidebar.width()
        
        if force_collapse:
            end_width = 0
        elif force_expand:
            end_width = 300
        else:
            end_width = 0 if width > 0 else 300
            
        if width == end_width:
            return

        self.anim_sidebar = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim_sidebar.setDuration(300)
        self.anim_sidebar.setStartValue(width)
        self.anim_sidebar.setEndValue(end_width)
        self.anim_sidebar.setEasingCurve(QEasingCurve.Type.InOutQuart)
        
        self.anim_sidebar_min = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim_sidebar_min.setDuration(300)
        self.anim_sidebar_min.setStartValue(width)
        self.anim_sidebar_min.setEndValue(end_width)
        self.anim_sidebar_min.setEasingCurve(QEasingCurve.Type.InOutQuart)
        
        self.anim_sidebar.start()
        self.anim_sidebar_min.start()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.hide()
        super().changeEvent(event)

    # ------- Mode & Refresh -------

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

    def refresh_view(self):
        # Clear existing items
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        query = self.search_input.text().strip().lower()
        apps = self._ordered_apps(query)
        self.filtered_apps = apps
        
        # Toggle Empty State
        if not apps and not query:
            self.scroll_area.hide()
            self.empty_state.show()
        else:
            self.empty_state.hide()
            self.scroll_area.show()

        callbacks = {
            "launch": self.launch_app,
            "toggle_fav": self.toggle_favorite,
            "edit": self.edit_app,
            "delete": self.delete_app
        }

        for app in apps:
            card = AppCardWidget(app, callbacks)
            
            # highlight favourites softly (extra border or glow)
            # highlight favourites softly (extra border or glow)
            if app.get("favorite"):
                card.setStyleSheet(
                    "#AppCard { border: 1px solid #fbbf24; background: #27272a; }"
                )
            
            self.flow_layout.addWidget(card)

        # suggestion / mode display
        if apps and query:
            top = apps[0]
            self.suggestion_label.setText(
                f"Top match: {top.get('name','App')} · {top.get('category','General')} (Enter to launch)"
            )
            self.suggestion_label.setVisible(True)
        else:
            self.suggestion_label.setVisible(False)

        self.update_tray_menu()
        self.update_sidebar_categories()

    def update_sidebar_categories(self):
        # Clear existing buttons
        while self.category_buttons_layout.count():
            item = self.category_buttons_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Get unique categories
        categories = sorted(list(set(app.get("category", "General") for app in self.apps)))
        if not categories:
            categories = ["General"]
            
        current_query = self.search_input.text().strip()
            
        # Add "All Apps" button
        all_btn = QPushButton("All Apps")
        all_btn.setObjectName("SidebarButton")
        all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        all_btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon)))
        
        # Active if no query and not in fav mode
        if not current_query and self.favorite_mode == 0:
            all_btn.setProperty("active", True)
            
        all_btn.clicked.connect(lambda: (self.search_input.clear(), self.set_favorite_mode(0)))
        self.category_buttons_layout.addWidget(all_btn)
        
        # Add "Favorites" button
        fav_btn = QPushButton("Favorites")
        fav_btn.setObjectName("SidebarButton")
        fav_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        fav_btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogYesButton)))
        
        # Active if in fav mode
        if self.favorite_mode != 0:
            fav_btn.setProperty("active", True)
            
        fav_btn.clicked.connect(lambda: self.toggle_favorite_mode())
        self.category_buttons_layout.addWidget(fav_btn)
        
        # Add category buttons
        for cat in categories:
            btn = QPushButton(cat)
            btn.setObjectName("SidebarButton")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIcon(QIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirIcon)))
            
            # Active if query matches category
            if current_query == cat:
                btn.setProperty("active", True)
                
            # Use default argument to capture current cat
            btn.clicked.connect(lambda checked, c=cat: (self.search_input.setText(c), self.set_favorite_mode(0)))
            self.category_buttons_layout.addWidget(btn)

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
            "category": category.strip(),
            "icon_path": "",
            "favorite": False
        }
        
        self.apps.append(app)
        self.next_id += 1
        self.save_config()
        self.refresh_view()
        self.show_toast(f"✓ Added {name.strip()}")



    def edit_app(self, app_id):
        app = self.get_app(app_id)
        if not app:
            return

        dialog = EditAppDialog(self, app)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.result_data
            
            app["name"] = data["name"]
            app["category"] = data["category"]
            app["path"] = data["path"]
            
            # Handle icon update
            new_icon_path = data["icon_path"]
            old_icon_path = app.get("icon_path")
            
            # If icon path changed and it's a valid file, we might want to copy it to our icons dir
            # or just use the path directly if the user prefers. 
            # For consistency with add_app, let's copy it if it's not already in our icons dir.
            if new_icon_path and new_icon_path != old_icon_path and os.path.exists(new_icon_path):
                try:
                    # Check if it's already in our icon dir to avoid re-copying own icons
                    if os.path.abspath(ICON_DIR) not in os.path.abspath(new_icon_path):
                        Path(ICON_DIR).mkdir(exist_ok=True)
                        ext = os.path.splitext(new_icon_path)[1] or ".png"
                        dst = os.path.join(ICON_DIR, f"{app['id']}{ext}")
                        shutil.copy2(new_icon_path, dst)
                        app["icon_path"] = dst
                    else:
                        app["icon_path"] = new_icon_path
                except Exception:
                    app["icon_path"] = new_icon_path # Fallback to original path on error
            elif not new_icon_path:
                app["icon_path"] = ""

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




# ---------- Entry ----------

def main():
    app = QApplication(sys.argv)
    window = AppLauncher()
    
    if window.settings.get("start_minimized", False):
        # Ensure tray icon is ready
        if window.tray_icon:
            window.show_toast("App started minimized")
        else:
            window.show()
    else:
        window.show()
        
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
