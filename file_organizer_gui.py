import os
import shutil
import logging
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import webbrowser # Added for the "Contact Us" feature

# --- Attempt to import Matplotlib ---
try:
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
    from matplotlib.ticker import FuncFormatter
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# --- Main Application Class (GUI and Backend Logic) ---
class FileOrganizerApp:
    """
    An all-in-one application to organize files in a directory
    with a clean graphical user interface and an advanced analytics dashboard.
    """

    def __init__(self, root):
        # --- App Info ---
        self.APP_VERSION = "2.0"

        # --- File Type Configuration ---
        self.FILE_TYPE_MAP = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".tiff"],
            "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx", ".odt", ".rtf"],
            "Videos": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"],
            "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Scripts": [".py", ".js", ".html", ".css", ".sh", ".bat"],
            "Others": []  # Default category for unclassified files
        }

        # --- Logging Setup ---
        logging.basicConfig(
            filename='file_organizer.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # --- State Management ---
        self.last_move_actions = [] # For the Undo feature

        # --- Window and Style Configuration ---
        self.root = root
        self.root.title("File Organizer Pro")
        self.root.geometry("1200x850") # Increased window size for more graphs
        self.root.configure(bg="#ffffff")
        self.root.resizable(True, True)

        # --- Theme Management ---
        self.is_dark_mode = True # Set dark mode as default
        self.themes = {
            "light": {
                "primary": "#32CD32", "secondary": "#ffffff", "text": "#333333",
                "accent": "#F0F0F0", "button_fg": "#ffffff"
            },
            "dark": {
                "primary": "#32CD32", "secondary": "#2E2E2E", "text": "#EAEAEA",
                "accent": "#3C3C3C", "button_fg": "#ffffff"
            }
        }
        self.font_title = ("Helvetica", 18, "bold")
        self.font_main = ("Helvetica", 11)

        # --- Initialize UI ---
        self.create_widgets()
        self.apply_theme("dark") # Apply dark theme on startup

    # --- Backend Logic ---
    def organize_directory(self, target_path: str, dry_run: bool = False):
        """
        Scans, analyzes, and organizes files into subfolders based on their extension.
        """
        def log_and_update(message: str, level: str = "info"):
            self.root.after(0, self.update_log_area, message)
            if level == "info": logging.info(message)
            elif level == "error": logging.error(message)
            elif level == "warning": logging.warning(message)
        
        log_prefix = "[DRY RUN] " if dry_run else ""
        log_and_update(f"🚀 {log_prefix}Starting organization process for: {target_path}")
        
        if not dry_run:
            self.last_move_actions.clear()

        analytics_data = {category: {'count': 0, 'size': 0} for category in self.FILE_TYPE_MAP.keys()}
        analytics_data["Others"] = {'count': 0, 'size': 0}
        files_processed_count = 0
        all_file_sizes = []

        try:
            all_items = os.listdir(target_path)
            
            for item_name in all_items:
                source_item_path = os.path.join(target_path, item_name)

                if item_name in ["file_organizer_app.py", "file_organizer.log"]:
                    continue

                if os.path.isdir(source_item_path):
                    log_and_update(f"Skipping: '{item_name}' (is a directory).")
                    continue
                
                try:
                    file_ext = os.path.splitext(item_name)[1].lower()
                    file_size = os.path.getsize(source_item_path)
                    all_file_sizes.append(file_size)
                    category = "Others"
                    for cat, exts in self.FILE_TYPE_MAP.items():
                        if file_ext in exts:
                            category = cat
                            break
                    analytics_data[category]['count'] += 1
                    analytics_data[category]['size'] += file_size
                except OSError as e:
                    log_and_update(f"Warning: Could not analyze '{item_name}': {e}", "warning")
                    continue

                dest_folder_path = os.path.join(target_path, category)
                final_dest_path = os.path.join(dest_folder_path, item_name)

                if dry_run:
                    log_and_update(f"{log_prefix}Would move: '{item_name}' -> '{category}'")
                    files_processed_count += 1
                else:
                    try:
                        os.makedirs(dest_folder_path, exist_ok=True)
                        shutil.move(source_item_path, final_dest_path)
                        log_and_update(f"Moved: '{item_name}' -> '{category}'")
                        self.last_move_actions.append((final_dest_path, source_item_path))
                        files_processed_count += 1
                    except shutil.Error as e:
                        log_and_update(f"Warning: Could not move '{item_name}'. It may already exist. Details: {e}", "warning")
                    except Exception as e:
                        log_and_update(f"Error moving '{item_name}': {e}", "error")

            if MATPLOTLIB_AVAILABLE:
                self.root.after(0, self.update_analytics_dashboard, analytics_data, all_file_sizes)
            
            if files_processed_count == 0:
                log_and_update("Info: No new files were found to organize.")

            log_and_update(f"✅ {log_prefix}Organization complete!")

        except Exception as e:
            log_and_update(f"An unexpected error occurred: {e}", "error")
        finally:
            self.root.after(0, self.finalize_organization, dry_run)

    def undo_last_organization(self):
        """Reverts the last set of file movements."""
        if not self.last_move_actions:
            messagebox.showinfo("Undo", "No actions to undo.")
            return

        def log_and_update(message: str):
            self.root.after(0, self.update_log_area, message)
            logging.info(message)

        log_and_update("⏪ Starting undo process...")
        self.undo_button.config(state="disabled")

        for source, dest in reversed(self.last_move_actions):
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.move(source, dest)
                log_and_update(f"Reverted: '{os.path.basename(source)}'")
            except Exception as e:
                log_and_update(f"Error undoing '{os.path.basename(source)}': {e}")
        
        log_and_update("✅ Undo complete!")
        self.last_move_actions.clear()

    # --- Frontend (GUI) Methods ---
    def create_widgets(self):
        """Creates and arranges all the GUI components in the window."""
        # --- Menu Bar ---
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About File Organizer", command=self.show_about_window)
        help_menu.add_command(label="Contact Support", command=self.contact_support)

        # --- Main Content ---
        self.container = tk.Frame(self.root)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        self.control_frame = tk.Frame(self.container, padx=10, pady=10)
        self.control_frame.pack(side="left", fill="y", expand=False)

        self.analytics_frame = tk.Frame(self.container, padx=10, pady=10)
        self.analytics_frame.pack(side="right", fill="both", expand=True)

        header_frame = tk.Frame(self.control_frame)
        header_frame.pack(fill="x", pady=(0, 20))
        self.title_label = tk.Label(header_frame, text="File Organizer", font=self.font_title)
        self.title_label.pack(side="left", anchor="w")
        self.dark_mode_switch = tk.Checkbutton(header_frame, text="☀️", font=self.font_main, command=self.toggle_dark_mode, relief="flat")
        self.dark_mode_switch.pack(side="right", anchor="e")
        self.dark_mode_switch.select() # Select the checkbox by default

        dir_frame = tk.Frame(self.control_frame)
        dir_frame.pack(fill="x", pady=10, anchor="w")
        self.dir_label = tk.Label(dir_frame, text="Target Directory:", font=self.font_main)
        self.dir_label.pack(side="left", padx=(0, 10))
        self.dir_entry = tk.Entry(dir_frame, font=self.font_main, bd=1, relief="solid", width=40)
        self.dir_entry.pack(side="left", expand=True, fill="x")
        self.browse_button = tk.Button(dir_frame, text="Browse", font=self.font_main, command=self.browse_directory, relief="flat", padx=10)
        self.browse_button.pack(side="left", padx=(10, 0))

        action_frame = tk.Frame(self.control_frame)
        action_frame.pack(fill="x", pady=20, anchor="w")
        self.organize_button = tk.Button(action_frame, text="Organize Files", font=self.font_main, command=self.start_organization_thread, relief="flat", width=20, pady=5)
        self.organize_button.pack(side="left", anchor="w")
        self.undo_button = tk.Button(action_frame, text="Undo Last Move", font=self.font_main, command=self.start_undo_thread, relief="flat", state="disabled")
        self.undo_button.pack(side="left", padx=(10,0))
        
        self.dry_run_var = tk.BooleanVar()
        self.dry_run_check = tk.Checkbutton(self.control_frame, text="Dry Run (Preview changes without moving files)", variable=self.dry_run_var, font=self.font_main)
        self.dry_run_check.pack(anchor="w")

        self.log_label = tk.Label(self.control_frame, text="Activity Log:", font=self.font_main)
        self.log_label.pack(anchor="w", pady=(10,0))
        self.log_area = scrolledtext.ScrolledText(self.control_frame, height=15, width=60, font=("Courier New", 10), bd=1, relief="solid", wrap=tk.WORD)
        self.log_area.pack(expand=True, fill="both", pady=(5, 0))
        self.log_area.insert(tk.END, "Welcome! Please select a directory to organize.\n")

        self.analytics_title = tk.Label(self.analytics_frame, text="Analytics Dashboard", font=self.font_title)
        self.analytics_title.pack(pady=(0, 10), anchor="w")
        
        if MATPLOTLIB_AVAILABLE:
            self.fig = Figure(figsize=(8, 8), dpi=100)
            (self.ax_bar, self.ax_pie), (self.ax_hist, self.ax_blank) = self.fig.subplots(2, 2)
            self.ax_blank.axis('off')
            
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.analytics_frame)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
            self.ax_bar.text(0.5, 0.5, 'File counts will be shown here.', ha='center', va='center')
            self.ax_pie.text(0.5, 0.5, 'File sizes will be shown here.', ha='center', va='center')
            self.ax_hist.text(0.5, 0.5, 'Size distribution will be shown here.', ha='center', va='center')
            self.canvas.draw()
        else:
            self.error_label = tk.Label(self.analytics_frame, text="Matplotlib not found.\nPlease run 'pip install matplotlib' for analytics.", font=self.font_main, fg="red", justify="center")
            self.error_label.pack(fill="both", expand=True)

    def show_about_window(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About File Organizer Pro")
        about_window.geometry("400x250")
        about_window.resizable(False, False)
        
        theme = self.themes['dark' if self.is_dark_mode else 'light']
        about_window.config(bg=theme['secondary'])
        
        title = tk.Label(about_window, text=f"File Organizer Pro v{self.APP_VERSION}", font=self.font_title, bg=theme['secondary'], fg=theme['primary'])
        title.pack(pady=20)
        
        description = tk.Label(about_window, text="This application helps you automatically organize\nfiles into folders based on their type.", font=self.font_main, bg=theme['secondary'], fg=theme['text'])
        description.pack(pady=10)

        copyright_info = tk.Label(about_window, text="© 2024 Your Company Name. All rights reserved.", font=("Helvetica", 9), bg=theme['secondary'], fg=theme['text'])
        copyright_info.pack(side="bottom", pady=10)

    def contact_support(self):
        subject = "File Organizer Pro - Support Request"
        mailto_link = f"mailto:support@example.com?subject={subject}"
        try:
            webbrowser.open(mailto_link)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open email client. Please email support@example.com.\n\nError: {e}")

    def format_size(self, size_bytes):
        if size_bytes == 0: return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB")
        import math
        i = int(math.floor(math.log(size_bytes, 1024))) if size_bytes > 0 else 0
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_name[i]}"

    def update_analytics_dashboard(self, data, all_file_sizes):
        self.ax_bar.clear()
        self.ax_pie.clear()
        self.ax_hist.clear()
        theme = self.themes['dark' if self.is_dark_mode else 'light']
        
        filtered_data = {cat: info for cat, info in data.items() if info['count'] > 0}

        if not filtered_data:
            self.ax_bar.text(0.5, 0.5, 'No files were processed.', ha='center', va='center', color=theme['text'])
            self.ax_pie.text(0.5, 0.5, '', ha='center', va='center')
            self.ax_hist.text(0.5, 0.5, '', ha='center', va='center')
            self.canvas.draw()
            return

        categories = list(filtered_data.keys())
        counts = [info['count'] for info in filtered_data.values()]
        self.ax_bar.bar(categories, counts, color=theme['primary'])
        self.ax_bar.set_title('File Count by Category', color=theme['text'])
        self.ax_bar.tick_params(axis='x', labelrotation=45, labelcolor=theme['text'], labelsize='small')
        self.ax_bar.tick_params(axis='y', labelcolor=theme['text'])

        sizes = [info['size'] for info in filtered_data.values()]
        total_size = sum(sizes)
        self.ax_pie.pie(sizes, labels=categories, autopct='%1.1f%%', startangle=90, textprops={'color': theme['text'], 'fontsize': 'small'})
        self.ax_pie.set_title(f'Total Size: {self.format_size(total_size)}', color=theme['text'])

        if all_file_sizes:
            filtered_sizes = [s for s in all_file_sizes if s > 0]
            if filtered_sizes:
                self.ax_hist.hist(filtered_sizes, bins=10, color=theme['primary'], log=True)
                self.ax_hist.set_xscale('log')
                self.ax_hist.xaxis.set_major_formatter(FuncFormatter(lambda x, pos: self.format_size(x)))
                self.ax_hist.set_title('File Size Distribution', color=theme['text'])
                self.ax_hist.tick_params(axis='x', labelrotation=45, labelcolor=theme['text'], labelsize='small')
                self.ax_hist.tick_params(axis='y', labelcolor=theme['text'])

        self.fig.tight_layout(pad=3.0)
        self.canvas.draw()

    def toggle_dark_mode(self):
        self.is_dark_mode = not self.is_dark_mode
        theme = "dark" if self.is_dark_mode else "light"
        self.dark_mode_switch.config(text="☀️" if self.is_dark_mode else "🌙")
        self.apply_theme(theme)

    def apply_theme(self, theme_name):
        theme = self.themes[theme_name]
        self.root.config(bg=theme['secondary'])
        
        for frame in [self.container, self.control_frame, self.analytics_frame, self.title_label.master, self.dir_label.master, self.organize_button.master]:
            frame.config(bg=theme['secondary'])

        for label in [self.title_label, self.dir_label, self.log_label, self.analytics_title]:
            label.config(bg=theme['secondary'], fg=theme['text'])

        self.dir_entry.config(bg=theme['accent'], fg=theme['text'], insertbackground=theme['text'])
        self.browse_button.config(bg=theme['primary'], fg=theme['button_fg'])
        self.organize_button.config(bg=theme['primary'], fg=theme['button_fg'])
        self.undo_button.config(bg=theme['accent'], fg=theme['text'])
        self.dark_mode_switch.config(bg=theme['secondary'], fg=theme['text'], selectcolor=theme['accent'])
        self.dry_run_check.config(bg=theme['secondary'], fg=theme['text'], selectcolor=theme['accent'])
        
        self.log_area.config(bg=theme['accent'], fg=theme['text'], insertbackground=theme['text'])
        if MATPLOTLIB_AVAILABLE:
            self.fig.patch.set_facecolor(theme['secondary'])
            for ax in [self.ax_bar, self.ax_pie, self.ax_hist]:
                ax.set_facecolor(theme['accent'])
                ax.title.set_color(theme['text'])
                for spine in ax.spines.values():
                    spine.set_edgecolor(theme['text'])
                ax.xaxis.label.set_color(theme['text'])
                ax.yaxis.label.set_color(theme['text'])
                ax.tick_params(axis='x', colors=theme['text'])
                ax.tick_params(axis='y', colors=theme['text'])
            self.canvas.draw()
        else:
            self.error_label.config(bg=theme['accent'])

    def browse_directory(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, folder_selected)

    def start_organization_thread(self):
        target_path = self.dir_entry.get()
        if not target_path or not os.path.isdir(target_path):
            messagebox.showerror("Error", "Please select a valid directory first.")
            return

        self.organize_button.config(state="disabled", text="Organizing...")
        self.undo_button.config(state="disabled")
        self.log_area.delete('1.0', tk.END)
        
        is_dry_run = self.dry_run_var.get()
        thread = threading.Thread(target=self.organize_directory, args=(target_path, is_dry_run), daemon=True)
        thread.start()
        
    def start_undo_thread(self):
        thread = threading.Thread(target=self.undo_last_organization, daemon=True)
        thread.start()

    def update_log_area(self, message):
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def finalize_organization(self, was_dry_run):
        self.organize_button.config(state="normal", text="Organize Files")
        if not was_dry_run and self.last_move_actions:
            self.undo_button.config(state="normal")

# --- Main Execution Block ---
if __name__ == "__main__":
    root = tk.Tk()
    app = FileOrganizerApp(root)
    root.mainloop()
