
# 📦 **App Launcher — Python + PyQt6**

A beautiful, modern, customizable **Unified Application Launcher** built with **Python + PyQt6** — featuring dual view modes, fuzzy search, favorites, system tray, and a fully interactive UI.

---

## ✨ **Features**

### 🎨 **Modern UI (Dark, Clean, Responsive)**

* Windows-11-style design
* Smooth animations
* Icon extraction from `.exe`
* Fully responsive layout
* High-DPI support

---

### 📚 **Two View Modes**

#### **Card Mode**

* Beautiful card layout
* App icon, name, category, path
* Launch / Edit / Delete buttons
* Favorite star with animation

#### **Compact Mode**

* Table-style view (like VSCode command palette)
* Resizable columns
* Icon + Name + Category + Path + Actions
* Clickable favorite star
* Very dense, fast navigation

Toggle using the **"Compact Mode"** button.

---

### 🔍 **Powerful Search**

* Instant fuzzy search
* Spotlight-style suggestion
* Press **Enter** to launch top match
* Matches app name + category
* Intelligent scoring system

---

### ⭐ **Upgraded Favorites System**

* Toggle fav instantly (card + compact mode)
* Star bounce animation
* Highlighted row for favorites
* Favorite sorting modes (`F` key):

  * Normal
  * Favorites First
  * Favorites Only

---

### 🖥️ **System Tray Integration**

* Minimize to tray
* Quick launch favorite apps
* Show/Hide with single click
* Exit from tray menu

---

### 🏷️ **App Management**

* Add apps manually
* Auto icon extraction
* Edit name & category
* Delete apps
* JSON-based storage
* Safe loading & saving

---

## 💻 **Installation**

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/app-launcher
cd app-launcher
```

### 2. Create virtual environment

```bash
python -m venv .venv
```

### 3. Activate venv

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install PyQt6
```

### 5. Run the launcher

```bash
python main.py
```

---

## 🎮 **Keyboard Shortcuts**

| Shortcut         | Action                  |
| ---------------- | ----------------------- |
| **Ctrl + P**     | Focus search bar        |
| **Ctrl + N**     | Add new app             |
| **Ctrl + Q**     | Quit app                |
| **Ctrl + ↑ / ↓** | Move selection          |
| **Ctrl + Enter** | Launch selected app     |
| **Enter**        | Launch top search match |
| **F**            | Cycle favorite modes    |
| **Esc**          | Close dialogs           |

---

## 🧠 **How App Data Works**

App data is stored in:

```
apps.json
```

Each entry includes:

```json
{
  "id": 1,
  "name": "VSCode",
  "path": "C:/Program Files/VSCode/Code.exe",
  "category": "Development",
  "favorite": true,
  "icon_path": "icons/1.png"
}
```

All icons are saved to:

```
icons/
```

---

## 📁 **Project Structure**

```
app-launcher/
│
├── main.py           # Main Launcher
├── apps.json         # App config (auto-generated)
├── icons/            # Extracted app icons
└── README.md         # Documentation
```

---

## 🖼️ **Screenshots**

(Add your own here)

```
![Card Mode](screenshots/card-mode.png)
![Compact Mode](screenshots/compact-mode.png)
![Search](screenshots/search.png)
```

---

## 🧩 **Roadmap**

* Global hotkey (bring launcher on top)
* Plugin system (scripts, websites)
* Categories sidebar
* Theme support (light/dark/custom)
* Export/Import config
* Auto-scan installed apps (optional)

---

## 🤝 **Contributing**

PRs are welcome!
If you improve UI/UX or add cool features, feel free to submit a pull request.

---

## 📝 **License**

MIT License.
Feel free to modify and use in your own projects.

---

## ❤️ **Author**

Made with love & caffeine ☕
By **Jeyaram** (and ChatGPT assist 😎)
