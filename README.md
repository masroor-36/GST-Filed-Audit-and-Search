Audit Folder & File (ZipCheckerApp)

A robust, multi-threaded desktop utility built with Python and tkinter designed for auditing directory structures, searching for specific files or patterns across root directories and nested subfolders, managing target subfolders, and batch-extracting ZIP archives using either built-in libraries or WinRAR.

🌟 Key Features

Dynamic UI Controls & Customization:

Comprehensive font family selector with dozens of typography options.

Quick font size scaling (A- / A+) with live-updating results view.

Root & Subfolder Tree Explorer:

Visualizes directory hierarchies in a clean tree structure (with or without nested subfolders).

Multi-threaded execution ensures the UI remains responsive during heavy file I/O scans.

Target Subfolder Management:

Automatically calculates previous month naming conventions (e.g., corporate financial calendar formats like YY-MM[MonthName]) or accepts custom folder names.

Dedicated tools to Search, Create, and Delete target subfolders across directories with safety confirmations.

Flexible File Searching:

Filter by precise names, wildcards (*.zip, *.pdf, *.xlsx), or partial matching.

Recursive search options to dig deep into nested directory trees.

Batch Unzipping / Extraction:

Detects .zip files in scan results and enables batch-extraction into individual target directories.

Prioritizes external WinRAR installation if available for accelerated performance, falling back gracefully to Python's standard zipfile module.

Abort Controls:

A real-time Stop button allows you to halt long-running scans or extractions safely at any point.

📋 Prerequisites

Python 3.x installed on your system.

Standard Python libraries used (included in standard installations):

tkinter, threading, pathlib, subprocess, zipfile, datetime.

Optional: WinRAR installed on Windows for optimized archive extraction.

🚀 Installation & Running

Clone or download the repository containing Audit File & Folder.py.

Open a terminal or command prompt in the directory containing the script.

Run the application using Python:

python "Audit File & Folder.py"


📖 Usage Guide

Root Folder: Select the parent directory you wish to audit using the Browse... button (defaults to the script's working directory).

Target Folder Name: Optionally specify a target subfolder name (pre-populated with the previous month's dynamic naming convention). Use buttons like Create Folder or Search to manage them.

File Pattern: Enter your target file extension or pattern (e.g., *.zip, invoice, *.pdf). Toggle the Sub Folder checkbox to enable deep recursive searches.

Search: Click Search to run the scan. Live results will stream into the main result window with color-coded summaries.

Unzip: If .zip files are discovered in the scan, the Unzip button will activate, allowing you to extract them into dedicated folders matching each archive's name.

🛠️ Code Architecture

The application is encapsulated within the ZipCheckerApp class adhering to standard object-oriented GUI design patterns in Tkinter:

UI Layout: Built using ttk themed widgets, responsive grid/pack geometry management, and text tagging for color-coded status reporting (green, blue, red, tree_root).

Concurrency: Long-running directory traversals and extraction tasks are offloaded to background daemon threads (threading.Thread) using thread-safe queue updates (root.after) to prevent GUI freezing.

📄 License

This project is open-source and available for internal tool auditing and personal workflow automation.
