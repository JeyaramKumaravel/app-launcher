# � **App Launcher — Premium Edition**

A stunning, modern, and highly customizable **Unified Application Launcher** built with **Python + PyQt6**. Featuring a premium dark theme, glassmorphism aesthetics, smooth animations, and a powerful fuzzy search engine.

---

## ✨ **New Premium Features**

### 🎨 **Premium UI Redesign**
* **Deep Dark Theme**: A rich "Zinc" color palette (`#09090b`) with vibrant Violet/Indigo accents.
* **Glassmorphism**: Subtle transparencies and blur effects for a modern feel.
* **Typography**: Clean, professional typography using system fonts (`Segoe UI` / `Inter`).
* **Animations**: Smooth hover effects, lift animations on cards, and fluid transitions.

### ⚙️ **Settings & Customization**
* **Minimize to Tray**: Option to keep the app running in the background when closed.
* **Start Minimized**: Launch the application silently to the system tray on startup.
* **Custom Toggle Switches**: Beautifully designed toggle controls for settings.

### � **Modern App Cards**
* **Clean Design**: Minimalist cards showing a large icon and the app name.
* **Smart Tooltips**: Hover to see category and detailed info.
* **Quick Actions**: Right-click context menu for Launch, Edit, Favorite, and Delete.
* **Favorites**: Star apps to pin them to the top or filter by favorites.

---

## � **Core Capabilities**

* **Fuzzy Search**: Instantly find apps by name or category with intelligent scoring.
* **Drag & Drop**: Simply drag `.exe` or shortcuts into the window to add them.
* **Sidebar Navigation**: Filter apps by category or view all with a single click.
* **System Tray**: Quick access to favorite apps and window controls from the tray.

---

## 💻 **Installation**

### 1. Clone the repo
```bash
git clone https://github.com/JeyaramKumaravel/app-launcher.git
cd app-launcher
```

### 2. Install dependencies
```bash
pip install PyQt6
```

### 3. Run the launcher
```bash
python main.py
```

---

## 🎮 **Keyboard Shortcuts**

| Shortcut | Action |
| :--- | :--- |
| **Ctrl + P** | Focus search bar |
| **Ctrl + N** | Add new app |
| **Ctrl + Q** | Quit application |
| **F** | Cycle favorite modes (Normal → Favs First → Favs Only) |
| **F1** | Show Shortcuts & Help |
| **Enter** | Launch top search match |

---

## 🧠 **How It Works**

App data is stored in `apps.json`.
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

## 🤝 **Contributing**

PRs are welcome! If you improve UI/UX or add cool features, feel free to submit a pull request.

---

## ❤️ **Author**

Made with love & caffeine ☕
By **Jeyaram**
