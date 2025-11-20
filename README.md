# 🎬 Media Files Manager

**Media Files Manager** is a sophisticated, all-in-one desktop utility built with **Python** and **PyQt6**. It streamlines complex media operations—such as downloading high-quality videos, manipulating PDFs, editing media metadata, and converting images—into a modern, responsive graphical user interface.

-----

## 🎨 Expert UI/UX Implementation

The graphical interface of this application was engineered with a focus on **modularity**, **responsiveness**, and **user experience**. Moving beyond basic widget placement, the UI implements several advanced PyQt6 techniques:

### 1\. Modern "Catppuccin" Design System

Instead of standard OS styling, the application injects a global, centralized **QSS (Qt Style Sheet)** configuration.

  * **Centralized Theme Constants:** Colors (`THEME_BG`, `THEME_ACCENT`, `THEME_CARD_BG`) are defined globally, ensuring consistency across all pages.
  * **Dark Mode Native:** The palette uses deep blues and soft pastels (e.g., `#1e1e2e` background, `#89b4fa` accents) to reduce eye strain and provide a professional aesthetic.
  * **High-Contrast Components:** Inputs, buttons, and progress bars utilize dynamic styling to ensure readability against the dark background.

### 2\. Component-Based Architecture

To maintain clean code and scalability, the UI is broken down into reusable custom components:

  * **Custom Cards:** Functionality isn't just dumped onto a form. Tools are encapsulated in interactive `QFrame` subclasses (e.g., `VideoToolCard`, `HomeCard`) that handle their own hover states, layout, and click events.
  * **Navigation Sidebar:** A custom-built sidebar uses `QButtonGroup` for exclusive state management, ensuring smooth transitions between views without the clutter of standard tab bars.

### 3\. Asynchronous Threading & Concurrency

The application remains perfectly responsive even during heavy tasks.

  * **QThread Implementation:** The `DownloadPage` utilizes `QThread` workers to run `yt-dlp` processes in the background.
  * **Signal/Slot Communication:** Custom signals (`pyqtSignal`) emit real-time progress, log messages, and completion statuses from the backend threads to the main UI thread, updating the GUI safely without freezing the window.

### 4\. Dynamic Layouts

  * **QStackedWidget:** Used for page navigation to keep the memory footprint low while allowing instant switching between tools.
  * **Responsive Grids:** The tools menus use `QGridLayout` and `QScrollArea` to adapt gracefully to different window sizes, ensuring the app looks good on laptops and large monitors alike.

-----

## 🚀 Key Features

  * **📥 Advanced Downloader:**
      * Download Videos and Audio from YouTube.
      * **Playlist Support:** Batch download entire playlists with quality selection (`1080p`, `4K`, `Audio Only`).
      * **Format Selection:** Visual table to select specific video/audio codecs and file sizes.
      * **Metadata & Subtitles:** Automatically embeds metadata and downloads subtitles.
  * **🎬 Video Editor:**
      * **Thumbnail Embedding:** Add custom covers to video files (Single or Batch).
      * **GIF Generator:** Create GIFs from specific video timestamps.
      * **Audio Extraction:** Rip high-quality audio tracks without re-encoding.

-----

## 🛠️ Installation

### Prerequisites

1.  **Python 3.10+** installed on your system.
2.  **FFmpeg** installed and added to your system PATH (Required for media processing).

### Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/media-files-manager.git
    cd media-files-manager
    ```

2.  **Install dependencies:**

    ```bash
    pip install PyQt6 yt-dlp Pillow PyMuPDF requests
    ```

3.  **Run the Application:**

    ```bash
    python main_gui.py
    ```

-----

## 📖 How to Use

### 1\. The Dashboard

Upon launching, you will see the **Home Dashboard**. Click on any card (e.g., "Download Media", "Edit Videos") or use the **Sidebar Icons** on the left to navigate.

### 2\. Downloading Media

1.  Navigate to the **Download** tab.
2.  Select **Single Video** or **Playlist**.
3.  Paste a YouTube URL and click **Fetch Info**.
4.  Review metadata (Title, Views, Duration).
5.  Click **Configure Download** to select quality, subtitles, or format.
6.  Click **Confirm Download**. The progress bar and log console will track the process.

### 3\. Batch Processing (Video/Audio/Images)

Many tools (like "Change Thumbnail" or "Extract Audio") offer a **Mode Selection**:

  * **Single File:** Select one specific file to process.
  * **Batch (Folder):** Select a directory. The app will process **every supported file** inside that folder automatically.

-----

## 📂 Project Structure

```text
QT6-GUI-Desktop-Application/
├── assets/                 # Icons and graphical resources
├── cli/                    # Backend Logic (The Brains)
│   ├── File.py             # Base file and directory handling
│   ├── video.py            # FFmpeg wrappers for video processing
│   ├── pdf.py              # PyMuPDF logic
│   ├── images.py           # Pillow logic for conversions
│   └── logs.py             # CSV logging system
├── gui/                    # Frontend Logic (The Face)
│   ├── main_window.py      # Application entry point and sidebar
│   └── pages/              # Individual feature pages
│       ├── home_page.py
│       ├── download_page.py
│       ├── video_page.py
│       ├── pdf_page.py
│       └── ...
└── main_gui.py             # Execution script
```

## 🤝 Contributing

Feel free to fork the project and submit Pull Requests. Ensure that any new heavy logic is handled in a separate thread to maintain UI responsiveness.

> This project is open-source. Please check the LICENSE file for details.
