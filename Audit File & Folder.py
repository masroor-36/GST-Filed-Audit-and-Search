import os
import subprocess
import zipfile
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from datetime import datetime, timedelta

class ZipCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audit Folder & File")
        self.root.geometry("900x740")
        self.root.minsize(580, 520)

        # Initial font size and family tracking
        self.current_font_size = 10
        self.current_font_family = "Courier"
        
        # Thread control flag to stop scans
        self.stop_requested = False
        
        # Store last found files for actions
        self.last_found_files = []
        self.last_query_type = "*.zip"
        
        # Store last searched subfolders for deletion
        self.last_searched_subfolders = []

        # Styling
        style = ttk.Style()
        style.theme_use("clam")

        # Main Frame
        main_frame = ttk.Frame(root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title and Font Controls Header Frame
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))

        title_label = ttk.Label(header_frame, text="Audit Folder & File", font=("Helvetica", 14, "bold"))
        title_label.pack(side=tk.LEFT)

        # Font Controls Frame (Dropdown + Size buttons)
        font_frame = ttk.Frame(header_frame)
        font_frame.pack(side=tk.RIGHT)

        ttk.Label(font_frame, text="Font:", font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(0, 4))
        
        # Comprehensive Font Family Dropdown (Sorted in Ascending Order)
        self.font_family_var = tk.StringVar(value=self.current_font_family)
        font_choices = sorted([
            "Agency FB", "Algerian", "Arial", "Arial Black", "Arial Narrow", "Arial Rounded MT Bold",
            "Bahnschrift", "Bodoni MT", "Book Antiqua", "Bookman Old Style", "Broadway", "Brush Script MT",
            "Calibri", "Calisto MT", "Cambria", "Candara", "Century", "Century Gothic", "Colonna MT",
            "Comic Sans MS", "Constantia", "Consolas", "Copperplate Gothic Bold", "Corbel",
            "Courier", "Courier New", "Curlz MT", "Ebrima", "Eras Bold ITC", "Fixedsys",
            "Footlight MT Light", "Franklin Gothic Medium", "Gabriola", "Garamond", "Georgia",
            "Harrington", "High Tower Text", "Helvetica", "Impact", "Kunstler Script",
            "Lucida Bright", "Lucida Console", "Lucida Sans Unicode", "Matura MT Script Capitals",
            "Microsoft Sans Serif", "Mistral", "Modern No. 20", "OCR A Extended", "Palatino Linotype",
            "Parchment", "Perpetua", "Playbill", "Ravie", "Rockwell", "Segoe UI", "Segoe UI Semibold",
            "Showcard Gothic", "Snap ITC", "Stencil", "Sylfaen", "Tahoma", "Times New Roman",
            "Trebuchet MS", "Verdana", "Viner Hand ITC", "Vivaldi", "Wide Latin"
        ])
        font_dropdown = ttk.Combobox(font_frame, textvariable=self.font_family_var, values=font_choices, width=22, state="readonly")
        font_dropdown.pack(side=tk.LEFT, padx=(0, 6))
        font_dropdown.bind("<<ComboboxSelected>>", self.change_font_family)
        
        btn_zoom_out = ttk.Button(font_frame, text=" A- ", width=3, command=self.decrease_font)
        btn_zoom_out.pack(side=tk.LEFT, padx=2)
        
        btn_zoom_in = ttk.Button(font_frame, text=" A+ ", width=3, command=self.increase_font)
        btn_zoom_in.pack(side=tk.LEFT, padx=2)

        # 1. Root Folder Selection with "Browse..." and "Folder Search" buttons on the right
        ttk.Label(main_frame, text="Root Folder:", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)
        
        frame_root = ttk.Frame(main_frame)
        frame_root.pack(fill=tk.X, pady=(2, 10))
        
        self.entry_root = ttk.Entry(frame_root, width=35)
        self.entry_root.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        current_script_dir = Path(__file__).resolve().parent
        self.entry_root.insert(0, str(current_script_dir))
        
        # Folder Search button on the right of Browse
        self.btn_sub_search = ttk.Button(frame_root, text="Folder Search", command=self.start_subfolder_tree_thread)
        self.btn_sub_search.pack(side=tk.RIGHT, padx=(2, 0))

        # Browse button
        btn_browse_root = ttk.Button(frame_root, text="Browse...", command=self.browse_root_folder)
        btn_browse_root.pack(side=tk.RIGHT, padx=(0, 2))

        # 2. Target Folder Name with Browse, Delete, Search, and Create Folder buttons on the right
        ttk.Label(main_frame, text="Target Folder Name (Optional - leave blank to search root only):", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)
        
        frame_folder = ttk.Frame(main_frame)
        frame_folder.pack(fill=tk.X, pady=(2, 10))
        
        self.entry_folder = ttk.Entry(frame_folder, width=26)
        self.entry_folder.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.entry_folder.insert(0, self.get_previous_month_folder_name())
        self.entry_folder.bind("<KeyRelease>", self.on_target_folder_typed)
        
        btn_browse_target = ttk.Button(frame_folder, text="Browse...", command=self.browse_target_folder)
        btn_browse_target.pack(side=tk.RIGHT, padx=(2, 0))

        # Delete Button (Default Disabled)
        self.btn_delete = ttk.Button(frame_folder, text="Delete", command=self.confirm_and_delete_subfolders, state=tk.DISABLED)
        self.btn_delete.pack(side=tk.RIGHT, padx=(2, 0))

        # Target Search Button
        self.btn_target_search = ttk.Button(frame_folder, text="Search", command=self.search_target_subfolders_prompt)
        self.btn_target_search.pack(side=tk.RIGHT, padx=(2, 0))

        # Create Folder Button
        self.btn_create_folder = ttk.Button(frame_folder, text="Create Folder", command=self.create_target_folder_prompt)
        self.btn_create_folder.pack(side=tk.RIGHT, padx=(2, 0))

        # 3. File Name Extension / Pattern / Partial Name
        ttk.Label(main_frame, text="File Name / Extension / Pattern (e.g., *.zip, *.jpg, invoice):", font=("Helvetica", 10, "bold")).pack(anchor=tk.W)
        
        frame_ext = ttk.Frame(main_frame)
        frame_ext.pack(fill=tk.X, pady=(2, 15))

        self.entry_ext = ttk.Entry(frame_ext, width=45)
        self.entry_ext.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry_ext.insert(0, "*.zip")

        # Sub Folder Checkbox (Right side of File Name input field) - using tk.Checkbutton for full font/color support
        self.subfolder_var = tk.BooleanVar(value=False)
        self.chk_subfolder = tk.Checkbutton(
            frame_ext, 
            text="✔ Sub Folder", 
            variable=self.subfolder_var, 
            command=self.on_subfolder_toggle,
            font=("Helvetica", 9, "bold"),
            selectcolor="#F9F9F9",
            activeforeground="#008000"
        )
        self.chk_subfolder.pack(side=tk.RIGHT)
        self.update_checkbox_color()

        # Action Buttons Frame (Search, Unzip, and Stop buttons)
        frame_actions = ttk.Frame(main_frame)
        frame_actions.pack(fill=tk.X, pady=(0, 15))

        self.btn_check = ttk.Button(frame_actions, text="Search", command=self.start_check_target_thread)
        self.btn_check.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5), ipady=5)

        self.btn_unzip = ttk.Button(frame_actions, text="Unzip", command=self.start_unzip_thread, state=tk.DISABLED)
        self.btn_unzip.pack(side=tk.LEFT, padx=5, ipadx=10, ipady=5)

        self.btn_stop = ttk.Button(frame_actions, text="Stop", command=self.stop_action, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.RIGHT, ipadx=15, ipady=5)

        # Result Display Area with Visible Vertical Scrollbar
        result_container = ttk.Frame(main_frame)
        result_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))

        scrollbar = ttk.Scrollbar(result_container, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.txt_result = tk.Text(result_container, wrap=tk.WORD, height=12, font=(self.current_font_family, self.current_font_size), bg="#F9F9F9", yscrollcommand=scrollbar.set)
        self.txt_result.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.txt_result.yview)
        
        # Configure tag colors
        self.update_tag_fonts()
        self.update_target_search_button_state()

        self.set_initial_message("Status: Ready. Click 'Search' or 'Folder Search' to begin.")

    def create_target_folder_prompt(self):
        target_name = self.entry_folder.get().strip()
        if not target_name:
            messagebox.showerror("Error", "Target Folder Name is blank.")
            return

        root_dir = self.entry_root.get().strip()
        if not root_dir:
            messagebox.showerror("Error", "Please select a Root Folder.")
            return

        root_path = Path(root_dir)
        if not root_path.exists():
            messagebox.showerror("Error", f"Root folder path does not exist:\n{root_path}")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Create Folder")
        dialog.geometry("520x220")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Where create:\n\"{target_name}\"", font=("Helvetica", 10, "bold"), justify=tk.CENTER).pack(pady=(15, 10))

        choice_var = tk.StringVar(value="root")

        path_root_str = str(root_path)
        path_sub_str = f"{root_path}\\ [Sub Folder]"

        rb1 = ttk.Radiobutton(dialog, text=path_root_str, variable=choice_var, value="root")
        rb1.pack(anchor=tk.W, padx=30, pady=4)

        rb2 = ttk.Radiobutton(dialog, text=path_sub_str, variable=choice_var, value="subfolders")
        rb2.pack(anchor=tk.W, padx=30, pady=4)

        def on_confirm():
            choice = choice_var.get()
            dialog.destroy()
            self.execute_create_folder(target_name, root_path, choice)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="Confirm", command=on_confirm, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def execute_create_folder(self, target_name, root_path, choice):
        self.stop_requested = False
        self.btn_sub_search.config(state=tk.DISABLED)
        self.btn_check.config(state=tk.DISABLED)
        self.btn_target_search.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)
        self.btn_create_folder.config(state=tk.DISABLED)
        self.btn_unzip.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self.set_initial_message(f"Creating folder '{target_name}'...\n")
        threading.Thread(target=lambda: self._run_create_folder(target_name, root_path, choice), daemon=True).start()

    def _run_create_folder(self, target_name, root_path, choice):
        try:
            target_folders_to_check = []
            if choice == "root":
                target_folders_to_check.append(root_path / target_name)
            elif choice == "subfolders":
                subdirs = sorted([p for p in root_path.iterdir() if p.is_dir()])
                for sub in subdirs:
                    target_folders_to_check.append(sub / target_name)

            if not target_folders_to_check:
                self.root.after(0, lambda: self.set_initial_message("No target locations found to create folders."))
                self.root.after(0, self.reset_buttons)
                return

            def init_ui():
                self.txt_result.config(state=tk.NORMAL)
                self.txt_result.delete("1.0", tk.END)
                header_title = f"============📂 Create Target Sub Folder : {target_name}=============\n"
                self.txt_result.insert(tk.END, header_title, "tree_root")
                self.txt_result.config(state=tk.DISABLED)

            self.root.after(0, init_ui)

            total_scan = len(target_folders_to_check)
            already_exit_count = 0
            success_count = 0

            for folder_path in target_folders_to_check:
                if self.stop_requested:
                    break

                parts_and_tags = [(f"📁 {folder_path}\n", "normal")]
                if folder_path.exists():
                    already_exit_count += 1
                    parts_and_tags.append(("            📁 Target Sub Folder Already Exit\n\n", "red"))
                else:
                    try:
                        folder_path.mkdir(parents=True, exist_ok=True)
                        success_count += 1
                        parts_and_tags.append(("            📁 Target Sub Folder created sucesfully\n\n", "green"))
                    except Exception as ex:
                        parts_and_tags.append((f"            [✖] Error: {ex}\n\n", "red"))

                self.root.after(0, lambda pat=parts_and_tags: self.append_multi_part_live(pat))

            if not self.stop_requested:
                summary_block = "="*44 + f"\n📁 Total Folder Scan: {total_scan}\n"
                summary_block += f"📁 Target Sub Folder Already Exit : {already_exit_count}\n"
                summary_block += f"📁 Target Sub Folder created sucesfully : {success_count}\n"
                self.root.after(0, lambda sb=summary_block: self.append_line_live(sb, "normal"))

            self.root.after(0, self.reset_buttons)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.reset_buttons)

    def search_target_subfolders_prompt(self):
        target_name = self.entry_folder.get().strip()
        if not target_name:
            messagebox.showerror("Error", "Target Folder Name is blank.")
            return

        root_dir = self.entry_root.get().strip()
        if not root_dir:
            messagebox.showerror("Error", "Please select a Root Folder.")
            return

        root_path = Path(root_dir)
        if not root_path.exists():
            messagebox.showerror("Error", f"Root folder path does not exist:\n{root_path}")
            return

        dialog = tk.Toplevel(self.root)
        dialog.title("Search Target Folder")
        dialog.geometry("520x220")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Where search:\n\"{target_name}\"", font=("Helvetica", 10, "bold"), justify=tk.CENTER).pack(pady=(15, 10))

        choice_var = tk.StringVar(value="root")

        path_root_str = str(root_path)
        path_sub_str = f"{root_path}\\ [Sub Folders]"

        rb1 = ttk.Radiobutton(dialog, text=path_root_str, variable=choice_var, value="root")
        rb1.pack(anchor=tk.W, padx=30, pady=4)

        rb2 = ttk.Radiobutton(dialog, text=path_sub_str, variable=choice_var, value="subfolders")
        rb2.pack(anchor=tk.W, padx=30, pady=4)

        def on_confirm():
            choice = choice_var.get()
            dialog.destroy()
            self.search_target_subfolders(target_name, root_path, choice)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=15)

        ttk.Button(btn_frame, text="Confirm", command=on_confirm, width=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy, width=10).pack(side=tk.LEFT, padx=5)

    def search_target_subfolders(self, target_name, root_path, choice):
        self.stop_requested = False
        self.btn_sub_search.config(state=tk.DISABLED)
        self.btn_check.config(state=tk.DISABLED)
        self.btn_target_search.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)
        self.btn_create_folder.config(state=tk.DISABLED)
        self.btn_unzip.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self.set_initial_message(f"Searching subfolders inside target '{target_name}'...\n")
        threading.Thread(target=lambda: self._run_target_subfolder_search(target_name, root_path, choice), daemon=True).start()

    def _run_target_subfolder_search(self, target_name, root_path, choice):
        try:
            if choice == "root":
                matching_folders = [root_path / target_name]
                matching_folders = [p for p in matching_folders if p.is_dir()]
            else:
                matching_folders = sorted([p for p in root_path.rglob(target_name) if p.is_dir()])

            if not matching_folders:
                self.root.after(0, lambda: self.set_initial_message(f"NOT FOUND: Target folder '{target_name}' does not exist."))
                self.root.after(0, self.reset_buttons)
                return

            def init_ui():
                self.txt_result.config(state=tk.NORMAL)
                self.txt_result.delete("1.0", tk.END)
                header_title = f"============📂 Target Subfolder Search: {target_name}=============\n"
                self.txt_result.insert(tk.END, header_title, "tree_root")
                self.txt_result.config(state=tk.DISABLED)

            self.root.after(0, init_ui)

            total_folders_scanned = len(matching_folders)
            sub_count_distribution = {}
            total_subs_found = 0
            
            self.last_searched_subfolders = []

            for folder in matching_folders:
                if self.stop_requested:
                    break

                folder_header = f"📁 {folder}\n"
                parts_and_tags = [(folder_header, "normal")]

                try:
                    subdirs = sorted([p for p in folder.iterdir() if p.is_dir()])
                except PermissionError:
                    subdirs = []

                num_subs = len(subdirs)
                total_subs_found += num_subs
                sub_count_distribution[num_subs] = sub_count_distribution.get(num_subs, 0) + 1

                for sub in subdirs:
                    self.last_searched_subfolders.append(sub)
                    parts_and_tags.append((f"            📁Sub Folder : {sub.name}\n", "normal"))

                if num_subs >= 2:
                    parts_and_tags.append((f"                           📁 {num_subs} Sub Folder Found\n\n", "green"))
                elif num_subs == 1:
                    parts_and_tags.append((f"                           📁 {num_subs} Sub Folder Found\n\n", "blue"))
                else:
                    parts_and_tags.append((f"                           📁 {num_subs} Sub Folder Found\n\n", "red"))

                self.root.after(0, lambda pat=parts_and_tags: self.append_multi_part_live(pat))

            if not self.stop_requested:
                summary_block = "="*44 + f"\n📁 Total Folder Scan: {total_folders_scanned}\n"
                
                sorted_counts = sorted(sub_count_distribution.keys(), reverse=True)
                for count in sorted_counts:
                    folder_qty = sub_count_distribution[count]
                    summary_block += f"📁 {count} Sub Folder Found Folder: {folder_qty}\n"

                summary_block += f"📁 {total_subs_found} Total Sub Folder Found\n"

                self.root.after(0, lambda sb=summary_block: self.append_line_live(sb, "normal"))

            self.root.after(0, self.reset_buttons)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.reset_buttons)

    def get_winrar_path(self):
        paths = [
            r"C:\Program Files\WinRAR\WinRAR.exe",
            r"C:\Program Files (x86)\WinRAR\WinRAR.exe"
        ]
        for p in paths:
            if Path(p).exists():
                return p
                
        try:
            import winreg
            reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\WinRAR.exe"
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                val = winreg.QueryValue(key, "")
                if val and Path(val).exists():
                    return val
        except Exception:
            pass
            
        if shutil_path := shutil.which("WinRAR.exe"):
            return shutil_path
            
        return None

    def update_checkbox_color(self):
        if self.subfolder_var.get():
            self.chk_subfolder.config(fg="#008000")
        else:
            self.chk_subfolder.config(fg="#333333")

    def update_target_search_button_state(self):
        if self.entry_folder.get().strip():
            self.btn_target_search.config(state=tk.NORMAL)
        else:
            self.btn_target_search.config(state=tk.DISABLED)

    def on_subfolder_toggle(self):
        self.update_checkbox_color()
        if self.subfolder_var.get():
            self.entry_folder.delete(0, tk.END)
        self.update_target_search_button_state()

    def on_target_folder_typed(self, event):
        target_val = self.entry_folder.get().strip()
        if target_val:
            self.subfolder_var.set(False)
            self.update_checkbox_color()
        self.update_target_search_button_state()

    def get_previous_month_folder_name(self):
        today = datetime.today()
        first_day_current = today.replace(day=1)
        prev_month_date = first_day_current - timedelta(days=1)
        
        p_year = prev_month_date.year
        p_month = prev_month_date.month
        p_month_name = prev_month_date.strftime('%B')
        
        if p_month >= 4:
            fy_start = p_year
            fy_end = p_year + 1
            serial = p_month - 3
        else:
            fy_start = p_year - 1
            fy_end = p_year
            serial = p_month + 9
            
        fy_str = f"{str(fy_start)[-2:]}-{str(fy_end)[-2:]}"
        return f"{fy_str} {serial:02d}{p_month_name}"

    def update_tag_fonts(self):
        fam = self.current_font_family
        sz = self.current_font_size
        self.txt_result.configure(font=(fam, sz))
        self.txt_result.tag_config("green", foreground="#008000", font=(fam, sz, "bold"))
        self.txt_result.tag_config("blue", foreground="#1D4ED8", font=(fam, sz, "bold"))
        self.txt_result.tag_config("red", foreground="#D32F2F", font=(fam, sz, "bold"))
        self.txt_result.tag_config("normal", foreground="#333333", font=(fam, sz))
        self.txt_result.tag_config("tree_root", foreground="#002B36", font=(fam, sz, "bold"))

    def change_font_family(self, event):
        self.current_font_family = self.font_family_var.get()
        self.update_tag_fonts()

    def increase_font(self):
        if self.current_font_size < 24:
            self.current_font_size += 1
            self.update_tag_fonts()

    def decrease_font(self):
        if self.current_font_size > 8:
            self.current_font_size -= 1
            self.update_tag_fonts()

    def browse_root_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.entry_root.delete(0, tk.END)
            self.entry_root.insert(0, folder_selected)

    def browse_target_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            folder_name = Path(folder_selected).name
            self.entry_folder.delete(0, tk.END)
            self.entry_folder.insert(0, folder_name)
            self.subfolder_var.set(False)
            self.update_checkbox_color()
            self.update_target_search_button_state()

    def set_initial_message(self, text):
        self.txt_result.config(state=tk.NORMAL)
        self.txt_result.delete("1.0", tk.END)
        self.txt_result.insert(tk.END, text, "normal")
        self.txt_result.config(state=tk.DISABLED)

    def stop_action(self):
        self.stop_requested = True
        self.append_line_live("\n[!] Search/Extraction stopped by user.\n", "red")
        self.reset_buttons()

    def start_subfolder_tree_thread(self):
        include_sub = messagebox.askyesno("Folder Search", "Search with Sub Folder?")
        
        self.stop_requested = False
        self.btn_sub_search.config(state=tk.DISABLED)
        self.btn_check.config(state=tk.DISABLED)
        self.btn_target_search.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)
        self.btn_create_folder.config(state=tk.DISABLED)
        self.btn_unzip.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        
        self.set_initial_message("Scanning folders (live progress)...\n")
        threading.Thread(target=lambda: self.show_subfolder_tree_live(include_sub), daemon=True).start()

    def confirm_and_delete_subfolders(self):
        target_name = self.entry_folder.get().strip()
        if not self.last_searched_subfolders:
            messagebox.showinfo("Delete", "No subfolders available to delete. Please run a Target Subfolder Search first.")
            return

        msg = f"Delete {target_name} -> Sub Folder ?"
        confirm = messagebox.askyesno("Confirm Delete", msg, icon=messagebox.WARNING)
        if not confirm:
            return

        self.stop_requested = False
        self.btn_sub_search.config(state=tk.DISABLED)
        self.btn_check.config(state=tk.DISABLED)
        self.btn_target_search.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)
        self.btn_create_folder.config(state=tk.DISABLED)
        self.btn_unzip.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        self.append_line_live("\n--- Starting Deletion ---\n", "tree_root")
        threading.Thread(target=self._execute_deletion, daemon=True).start()

    def _execute_deletion(self):
        try:
            deleted_count = 0
            import shutil
            for sub_path in self.last_searched_subfolders:
                if self.stop_requested:
                    break
                if sub_path.exists() and sub_path.is_dir():
                    try:
                        shutil.rmtree(sub_path)
                        deleted_count += 1
                        msg = f"[✔] Deleted Sub Folder: {sub_path.name}\n"
                        self.root.after(0, lambda m=msg: self.append_line_live(m, "green"))
                    except Exception as ex:
                        err_msg = f"[✖] Failed to delete {sub_path.name}: {ex}\n"
                        self.root.after(0, lambda em=err_msg: self.append_line_live(em, "red"))

            if not self.stop_requested:
                finish_msg = f"\n--- Deletion Complete! Successfully deleted {deleted_count} subfolder(s). ---\n"
                self.root.after(0, lambda fm=finish_msg: self.append_line_live(fm, "tree_root"))
                self.last_searched_subfolders = []

            self.root.after(0, self.reset_buttons)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.reset_buttons)

    def show_subfolder_tree_live(self, include_sub):
        try:
            root_dir = self.entry_root.get().strip()
            if not root_dir:
                self.root.after(0, lambda: messagebox.showerror("Error", "Please select a Root Folder."))
                self.root.after(0, self.reset_buttons)
                return

            root_path = Path(root_dir)
            if not root_path.exists():
                self.root.after(0, lambda: messagebox.showerror("Error", f"Root folder path does not exist:\n{root_path}"))
                self.root.after(0, self.reset_buttons)
                return

            try:
                direct_subdirs = sorted([p for p in root_path.iterdir() if p.is_dir()])
                total_root_folders = len(direct_subdirs)
            except PermissionError:
                total_root_folders = 0

            def init_ui():
                self.txt_result.config(state=tk.NORMAL)
                self.txt_result.delete("1.0", tk.END)
                self.txt_result.insert(tk.END, f"📂 Root: {root_path}\n", "tree_root")
                self.txt_result.config(state=tk.DISABLED)

            self.root.after(0, init_ui)

            if not include_sub:
                for sub in direct_subdirs:
                    if self.stop_requested:
                        break
                    line = f"├── {sub.name}\n"
                    self.root.after(0, lambda l=line: self.append_line_live(l, "normal"))
            else:
                def build_tree_recursive(current_path, prefix=""):
                    if self.stop_requested:
                        return
                    try:
                        subdirs = sorted([p for p in current_path.iterdir() if p.is_dir()])
                    except PermissionError:
                        return
                    
                    for i, sub in enumerate(subdirs):
                        if self.stop_requested:
                            break
                        is_last = (i == len(subdirs) - 1)
                        connector = "└── " if is_last else "├── "
                        line = f"{prefix}{connector}{sub.name}\n"
                        
                        self.root.after(0, lambda l=line: self.append_line_live(l, "normal"))
                        
                        extension = "    " if is_last else "│   "
                        build_tree_recursive(sub, prefix + extension)

                build_tree_recursive(root_path)

            if not self.stop_requested:
                total_msg = f"\n=====================\n📁 Total Folder : {total_root_folders}\n"
                self.root.after(0, lambda: self.append_line_live(total_msg, "tree_root"))
            
            self.root.after(0, self.reset_buttons)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.reset_buttons)

    def append_line_live(self, text, tag="normal"):
        self.txt_result.config(state=tk.NORMAL)
        self.txt_result.insert(tk.END, text, tag)
        self.txt_result.see(tk.END)
        self.txt_result.config(state=tk.DISABLED)

    def append_multi_part_live(self, parts_and_tags):
        self.txt_result.config(state=tk.NORMAL)
        for text, tag in parts_and_tags:
            self.txt_result.insert(tk.END, text, tag)
        self.txt_result.see(tk.END)
        self.txt_result.config(state=tk.DISABLED)

    def reset_buttons(self):
        self.btn_sub_search.config(state=tk.NORMAL)
        self.btn_check.config(state=tk.NORMAL)
        self.update_target_search_button_state()
        self.btn_create_folder.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        
        if self.last_searched_subfolders:
            self.btn_delete.config(state=tk.NORMAL)
        else:
            self.btn_delete.config(state=tk.DISABLED)

        zips_available = any(f.suffix.lower() == '.zip' for f in self.last_found_files)
        if zips_available:
            self.btn_unzip.config(state=tk.NORMAL)
        else:
            self.btn_unzip.config(state=tk.DISABLED)

    def start_check_target_thread(self):
        self.stop_requested = False
        self.last_found_files = []
        self.btn_sub_search.config(state=tk.DISABLED)
        self.btn_check.config(state=tk.DISABLED)
        self.btn_target_search.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)
        self.btn_create_folder.config(state=tk.DISABLED)
        self.btn_unzip.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        
        self.set_initial_message("Searching files... (live output)\n")
        threading.Thread(target=self.check_target_live, daemon=True).start()

    def check_target_live(self):
        try:
            root_dir = self.entry_root.get().strip()
            target_folder_name = self.entry_folder.get().strip()
            file_query = self.entry_ext.get().strip()
            search_sub_checked = self.subfolder_var.get()
            self.last_query_type = file_query

            if not root_dir:
                self.root.after(0, lambda: messagebox.showerror("Error", "Please select a Root Folder."))
                self.root.after(0, self.reset_buttons)
                return
            if not file_query:
                self.root.after(0, lambda: messagebox.showerror("Error", "Please provide a file name or pattern."))
                self.root.after(0, self.reset_buttons)
                return

            root_path = Path(root_dir)
            if not root_path.exists():
                self.root.after(0, lambda: messagebox.showerror("Error", f"Root folder path does not exist:\n{root_path}"))
                self.root.after(0, self.reset_buttons)
                return

            if not target_folder_name:
                if search_sub_checked:
                    all_subdirs = sorted([p for p in root_path.rglob('*') if p.is_dir()])
                    all_subdirs.insert(0, root_path)
                else:
                    all_subdirs = [root_path]
            else:
                all_subdirs = sorted([p for p in root_path.iterdir() if p.is_dir()])

            if self.stop_requested:
                self.reset_buttons()
                return

            def clear_res():
                self.txt_result.config(state=tk.NORMAL)
                self.txt_result.delete("1.0", tk.END)
                header_title = f"============ 📦 Target ({file_query}) file Search ============\n"
                self.txt_result.insert(tk.END, header_title, "tree_root")
                self.txt_result.config(state=tk.DISABLED)

            self.root.after(0, clear_res)

            if not target_folder_name and search_sub_checked:
                total_folders = len([p for p in all_subdirs if p != root_path])
            else:
                total_folders = len(all_subdirs)

            target_found_count = 0
            file_count_distribution = {}

            for folder in all_subdirs:
                if self.stop_requested:
                    break

                if target_folder_name:
                    target_path = folder / target_folder_name
                    exists = target_path.is_dir()
                    if exists:
                        target_found_count += 1
                        search_folder = target_path
                    else:
                        search_folder = None
                else:
                    exists = True
                    target_found_count += 1
                    search_folder = folder

                folder_display_str = f"📁 {folder}\n"
                parts_and_tags = [(folder_display_str, "normal")]

                if target_folder_name:
                    if exists:
                        parts_and_tags.append(("Target Folder Exit : ", "normal"))
                        parts_and_tags.append(("Yes\n", "green"))
                    else:
                        parts_and_tags.append(("Target Folder Exit : ", "normal"))
                        parts_and_tags.append(("No\n", "red"))

                files_in_folder = []
                if search_folder and search_folder.is_dir():
                    try:
                        if "*" in file_query or "?" in file_query:
                            q_lower = file_query.lower()
                            q_upper = file_query.upper()
                            matched_set = set()
                            for p in search_folder.glob(q_lower):
                                if p.is_file(): matched_set.add(p)
                            for p in search_folder.glob(q_upper):
                                if p.is_file(): matched_set.add(p)
                            if q_lower.startswith("*."):
                                ext = q_lower[1:]
                                for p in search_folder.iterdir():
                                    if p.is_file() and p.suffix.lower() == ext:
                                        matched_set.add(p)
                            files_in_folder = sorted(list(matched_set))
                        else:
                            all_files = [p for p in search_folder.iterdir() if p.is_file()]
                            files_in_folder = [p for p in all_files if file_query.lower() in p.name.lower()]
                    except PermissionError:
                        pass

                for fp in files_in_folder:
                    self.last_found_files.append(fp)

                num_files = len(files_in_folder)
                file_count_distribution[num_files] = file_count_distribution.get(num_files, 0) + 1

                if num_files > 0:
                    for fp in files_in_folder:
                        parts_and_tags.append((f"📦 File Name: {fp.name}\n", "normal"))
                
                if num_files >= 2:
                    parts_and_tags.append((f"            📦 {num_files} File Found\n\n", "green"))
                elif num_files == 1:
                    parts_and_tags.append((f"            📦 {num_files} File Found\n\n", "blue"))
                else:
                    parts_and_tags.append((f"            📦 0 File Found\n\n", "red"))

                self.root.after(0, lambda pat=parts_and_tags: self.append_multi_part_live(pat))

            if not self.stop_requested:
                summary_block = "="*44 + "\n"
                summary_block += f"📁 Total Folder Scan: {total_folders}\n"
                
                if target_folder_name:
                    summary_block += f"Target Folder Found : {target_found_count}\n"

                sorted_counts = sorted(file_count_distribution.keys(), reverse=True)
                for count in sorted_counts:
                    folder_qty = file_count_distribution[count]
                    summary_block += f"📦 {count} File Found Folder: {folder_qty}\n"

                q_lower = file_query.lower().strip()
                if q_lower.startswith("*.") or q_lower.startswith("."):
                    ext_name = q_lower.replace("*", "").replace(".", "").upper()
                    if ext_name == "ZIP":
                        file_label = "Zip File"
                    elif ext_name in ("PDF",):
                        file_label = "PDF File"
                    elif ext_name in ("XLS", "XLSX", "CSV"):
                        file_label = "Excel File"
                    elif ext_name in ("JPG", "JPEG", "PNG", "GIF"):
                        file_label = "JPG File"
                    elif ext_name in ("DOC", "DOCX"):
                        file_label = "Word File"
                    elif ext_name in ("TXT",):
                        file_label = "Text File"
                    else:
                        file_label = f"{ext_name} File"
                else:
                    file_label = "File"

                total_files_count = len(self.last_found_files)
                summary_block += f"📦 {total_files_count} Total {file_label} found\n"

                zips_present = any(f.suffix.lower() == '.zip' for f in self.last_found_files)
                if zips_present:
                    summary_block += f"\n[i] Click 'Unzip' to extract discovered zip file(s).\n"

                self.root.after(0, lambda sb=summary_block: self.append_line_live(sb, "normal"))

            self.root.after(0, self.reset_buttons)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.reset_buttons)

    def start_unzip_thread(self):
        zip_files_only = [f for f in self.last_found_files if f.suffix.lower() == '.zip']
        if not zip_files_only:
            messagebox.showinfo("Unzip", "No zip files available to extract.")
            return

        if not messagebox.askyesno("Confirm Unzip", f"Extract {len(zip_files_only)} zip file(s) into folders with their respective names?"):
            return

        self.stop_requested = False
        self.btn_sub_search.config(state=tk.DISABLED)
        self.btn_check.config(state=tk.DISABLED)
        self.btn_target_search.config(state=tk.DISABLED)
        self.btn_delete.config(state=tk.DISABLED)
        self.btn_create_folder.config(state=tk.DISABLED)
        self.btn_unzip.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

        def clear_res():
            self.txt_result.config(state=tk.NORMAL)
            self.txt_result.delete("1.0", tk.END)
            self.txt_result.config(state=tk.DISABLED)

        self.root.after(0, clear_res)
        threading.Thread(target=lambda: self.unzip_files_grouped_live(zip_files_only), daemon=True).start()

    def unzip_files_grouped_live(self, zip_files_only):
        try:
            root_dir = self.entry_root.get().strip()
            root_path = Path(root_dir)
            winrar_exe = self.get_winrar_path()

            folder_groups = {}
            for zip_path in zip_files_only:
                parent_folder = zip_path.parent
                if parent_folder not in folder_groups:
                    folder_groups[parent_folder] = []
                folder_groups[parent_folder].append(zip_path)

            total_folders_unzipped = len(folder_groups)
            total_files_unzipped = 0

            for folder_path, zips in folder_groups.items():
                if self.stop_requested:
                    break

                header_line = f"📁 {folder_path}\n"
                self.root.after(0, lambda h=header_line: self.append_line_live(h, "tree_root"))

                folder_success_count = 0
                for zip_path in zips:
                    if self.stop_requested:
                        break
                    
                    file_line = f"📦 File Name: {zip_path.name}\n"
                    self.root.after(0, lambda fl=file_line: self.append_line_live(fl, "normal"))

                    extract_dir = zip_path.parent / zip_path.stem
                    extract_dir.mkdir(exist_ok=True)

                    try:
                        if winrar_exe:
                            cmd = [winrar_exe, "x", str(zip_path), str(extract_dir) + "\\"]
                            subprocess.run(cmd, check=True)
                        else:
                            with zipfile.ZipFile(zip_path, 'r') as zf:
                                zf.extractall(extract_dir)

                        folder_success_count += 1
                        total_files_unzipped += 1
                        
                        unzip_to_line = f"📁 Unzip To : {extract_dir.name}\n"
                        self.root.after(0, lambda ut=unzip_to_line: self.append_line_live(ut, "normal"))
                    except Exception as ex:
                        err_line = f"[✖] Failed to extract {zip_path.name}: {ex}\n"
                        self.root.after(0, lambda el=err_line: self.append_line_live(el, "red"))

                if folder_success_count >= 2:
                    status_line = f"            📦 {folder_success_count} File Unzip\n\n"
                    tag = "green"
                elif folder_success_count == 1:
                    status_line = f"            📦 {folder_success_count} File Unzip\n\n"
                    tag = "blue"
                else:
                    status_line = f"            📦 0 File Unzip\n\n"
                    tag = "red"

                self.root.after(0, lambda sl=status_line, t=tag: self.append_line_live(sl, t))

            if not self.stop_requested:
                summary_block = "="*59 + f"\n📁 Total Folder Scan: {total_folders_unzipped}\n"
                summary_block += f"📦 Total File Unzip: {total_files_unzipped}\n"
                self.root.after(0, lambda sb=summary_block: self.append_line_live(sb, "normal"))

            self.root.after(0, self.reset_buttons)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.root.after(0, self.reset_buttons)

if __name__ == "__main__":
    root = tk.Tk()
    app = ZipCheckerApp(root)
    root.mainloop()
