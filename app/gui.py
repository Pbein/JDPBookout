"""
Main GUI application for JD Power PDF Downloader.
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import queue
import time
from datetime import datetime

from app.worker import DownloadWorker
from app.settings import (
    save_credentials, load_credentials, delete_credentials,
    save_preferences, load_preferences, save_last_username
)
from app.utils import (
    validate_credentials, validate_folder,
    format_time, format_progress, calculate_speed, estimate_remaining_time
)


class JDPowerApp:
    """Main GUI application for JD Power PDF Downloader."""
    
    def __init__(self, root):
        """
        Initialize the GUI application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("JD Power PDF Downloader")
        
        # Load preferences
        self.prefs = load_preferences()
        
        # Set window size
        window_width = self.prefs.get("window_width", 650)
        window_height = self.prefs.get("window_height", 750)
        self.root.geometry(f"{window_width}x{window_height}")
        
        # Set minimum size
        self.root.minsize(600, 700)
        
        # Worker thread and queue
        self.worker = None
        self.result_queue = queue.Queue()
        
        # Progress tracking
        self.start_time = None
        self.total_items = 0
        self.processed = 0
        self.succeeded = 0
        self.failed = 0
        
        # Create GUI
        self.create_widgets()
        self.load_saved_settings()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create all GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        row = 0
        
        # Title
        title_label = ttk.Label(main_frame, text="JD Power PDF Downloader", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=row, column=0, pady=(0, 20))
        row += 1
        
        # === Credentials Section ===
        cred_frame = ttk.LabelFrame(main_frame, text=" Login Credentials ", padding="10")
        cred_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        cred_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Username
        ttk.Label(cred_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(cred_frame, width=40)
        self.username_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Password
        ttk.Label(cred_frame, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.password_entry = ttk.Entry(cred_frame, width=40, show="*")
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Save credentials checkbox
        self.save_creds_var = tk.BooleanVar(value=self.prefs.get("save_credentials", False))
        save_creds_check = ttk.Checkbutton(cred_frame, text="Remember credentials (stored securely)",
                                          variable=self.save_creds_var)
        save_creds_check.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        # === Download Location Section ===
        loc_frame = ttk.LabelFrame(main_frame, text=" Download Location ", padding="10")
        loc_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        loc_frame.columnconfigure(0, weight=1)
        row += 1
        
        folder_container = ttk.Frame(loc_frame)
        folder_container.grid(row=0, column=0, sticky=(tk.W, tk.E))
        folder_container.columnconfigure(0, weight=1)
        
        self.folder_entry = ttk.Entry(folder_container, width=50)
        self.folder_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = ttk.Button(folder_container, text="Browse...", command=self.browse_folder)
        browse_btn.grid(row=0, column=1)
        
        # === Options Section ===
        options_frame = ttk.LabelFrame(main_frame, text=" Options ", padding="10")
        options_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        options_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Max downloads
        ttk.Label(options_frame, text="Max Downloads:").grid(row=0, column=0, sticky=tk.W, pady=5)
        max_frame = ttk.Frame(options_frame)
        max_frame.grid(row=0, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.max_downloads_var = tk.StringVar(value=str(self.prefs.get("max_downloads", 0)))
        max_spin = ttk.Spinbox(max_frame, from_=0, to=10000, textvariable=self.max_downloads_var, width=10)
        max_spin.grid(row=0, column=0)
        ttk.Label(max_frame, text="(0 = download all)").grid(row=0, column=1, padx=(10, 0))
        
        # Number of workers
        ttk.Label(options_frame, text="Parallel Workers:").grid(row=1, column=0, sticky=tk.W, pady=5)
        workers_frame = ttk.Frame(options_frame)
        workers_frame.grid(row=1, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        self.num_workers_var = tk.StringVar(value=str(self.prefs.get("num_workers", 5)))
        workers_spin = ttk.Spinbox(workers_frame, from_=1, to=10, textvariable=self.num_workers_var, width=10)
        workers_spin.grid(row=0, column=0)
        ttk.Label(workers_frame, text="(5-7 recommended)").grid(row=0, column=1, padx=(10, 0))
        
        # Headless mode
        self.headless_var = tk.BooleanVar(value=self.prefs.get("headless", True))
        headless_check = ttk.Checkbutton(options_frame, text="Run browser in background (headless mode)",
                                        variable=self.headless_var)
        headless_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # === Control Buttons ===
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=row, column=0, pady=20)
        row += 1
        
        self.start_btn = tk.Button(btn_frame, text="START DOWNLOAD",
                                   bg="#4CAF50", fg="white",
                                   font=("Arial", 12, "bold"),
                                   width=20, height=2,
                                   command=self.start_download,
                                   cursor="hand2")
        self.start_btn.grid(row=0, column=0, padx=10)
        
        self.stop_btn = tk.Button(btn_frame, text="STOP",
                                  bg="#f44336", fg="white",
                                  font=("Arial", 12, "bold"),
                                  width=20, height=2,
                                  command=self.stop_download,
                                  state="disabled",
                                  cursor="hand2")
        self.stop_btn.grid(row=0, column=1, padx=10)
        
        # === Progress Section ===
        prog_frame = ttk.LabelFrame(main_frame, text=" Progress ", padding="10")
        prog_frame.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        prog_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(row, weight=1)
        row += 1
        
        # Status label
        self.status_label = ttk.Label(prog_frame, text="Ready to start", 
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(prog_frame, mode="determinate", length=500)
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Progress text
        self.progress_text = ttk.Label(prog_frame, text="0/0 PDFs downloaded (0%)",
                                      font=("Arial", 9))
        self.progress_text.grid(row=2, column=0, pady=5)
        
        # Stats frame
        stats_frame = ttk.Frame(prog_frame)
        stats_frame.grid(row=3, column=0, pady=10)
        
        self.time_label = ttk.Label(stats_frame, text="Time Elapsed: 0s")
        self.time_label.grid(row=0, column=0, padx=20)
        
        self.speed_label = ttk.Label(stats_frame, text="Speed: -- /hour")
        self.speed_label.grid(row=0, column=1, padx=20)
        
        self.remaining_label = ttk.Label(stats_frame, text="Est. Remaining: --")
        self.remaining_label.grid(row=0, column=2, padx=20)
        
        # Counters frame
        counters_frame = ttk.Frame(prog_frame)
        counters_frame.grid(row=4, column=0, pady=5)
        
        self.success_label = ttk.Label(counters_frame, text="Succeeded: 0", foreground="green")
        self.success_label.grid(row=0, column=0, padx=20)
        
        self.failed_label = ttk.Label(counters_frame, text="Failed: 0", foreground="red")
        self.failed_label.grid(row=0, column=1, padx=20)
        
        # Log area
        log_label = ttk.Label(prog_frame, text="Activity Log:", font=("Arial", 9, "bold"))
        log_label.grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        
        self.log_text = scrolledtext.ScrolledText(prog_frame, height=12, 
                                                  font=("Consolas", 8), wrap=tk.WORD)
        self.log_text.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        prog_frame.rowconfigure(6, weight=1)
    
    def browse_folder(self):
        """Open folder browser dialog."""
        folder = filedialog.askdirectory(title="Select Download Folder")
        if folder:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder)
    
    def load_saved_settings(self):
        """Load saved settings into GUI fields."""
        # Load last username
        last_username = self.prefs.get("last_username", "")
        if last_username:
            self.username_entry.insert(0, last_username)
            
            # Try to load saved password
            if self.prefs.get("save_credentials", False):
                saved_password = load_credentials(last_username)
                if saved_password:
                    self.password_entry.insert(0, saved_password)
        
        # Load download folder
        download_folder = self.prefs.get("download_folder", "")
        if download_folder:
            self.folder_entry.insert(0, download_folder)
    
    def start_download(self):
        """Start the download process."""
        # Validate inputs
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        download_folder = self.folder_entry.get().strip()
        
        # Validate credentials
        valid, error_msg = validate_credentials(username, password)
        if not valid:
            messagebox.showerror("Invalid Input", error_msg)
            return
        
        # Validate folder
        valid, error_msg = validate_folder(download_folder)
        if not valid:
            messagebox.showerror("Invalid Folder", error_msg)
            return
        
        # Get options
        try:
            max_downloads = int(self.max_downloads_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Max downloads must be a number")
            return
        
        try:
            num_workers = int(self.num_workers_var.get())
            if num_workers < 1 or num_workers > 10:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Invalid Input", "Number of workers must be between 1 and 10")
            return
        
        headless = self.headless_var.get()
        
        # Save preferences
        save_creds = self.save_creds_var.get()
        self.prefs.update({
            "last_username": username,
            "download_folder": download_folder,
            "save_credentials": save_creds,
            "max_downloads": max_downloads,
            "num_workers": num_workers,
            "headless": headless,
        })
        save_preferences(self.prefs)
        save_last_username(username)
        
        # Save or delete credentials
        if save_creds:
            save_credentials(username, password)
            self.log("Credentials saved securely")
        else:
            delete_credentials(username)
        
        # Reset progress
        self.start_time = time.time()
        self.processed = 0
        self.succeeded = 0
        self.failed = 0
        self.progress_bar["value"] = 0
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Start worker thread
        self.worker = DownloadWorker(
            username=username,
            password=password,
            download_folder=download_folder,
            max_downloads=max_downloads,
            num_workers=num_workers,
            headless=headless,
            result_queue=self.result_queue
        )
        self.worker.start()
        
        # Update UI
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_label.config(text="Starting download process...")
        self.log("Starting download process...")
        self.log(f"Download location: {download_folder}")
        self.log(f"Max downloads: {max_downloads if max_downloads > 0 else 'All'}")
        self.log(f"Parallel workers: {num_workers}")
        self.log(f"Headless mode: {'Yes' if headless else 'No'}")
        self.log("-" * 60)
        
        # Start checking queue
        self.check_queue()
        self.update_stats()
    
    def stop_download(self):
        """Stop the download process."""
        if self.worker:
            self.worker.stop()
            self.log("Stop requested. Finishing current task...")
            self.status_label.config(text="Stopping...")
    
    def check_queue(self):
        """Check the result queue for updates from worker thread."""
        try:
            while True:  # Process all available messages
                result = self.result_queue.get_nowait()
                self.handle_result(result)
        except queue.Empty:
            pass
        
        # Check again in 100ms if worker is still alive
        if self.worker and self.worker.is_alive():
            self.root.after(100, self.check_queue)
    
    def handle_result(self, result):
        """
        Handle a result message from the worker thread.
        
        Args:
            result: Dictionary with 'type' and other fields
        """
        result_type = result.get('type', '')
        
        if result_type == 'start':
            self.log(result.get('message', 'Started'))
        
        elif result_type == 'progress':
            self.processed = result.get('processed', 0)
            self.succeeded = result.get('succeeded', 0)
            self.failed = result.get('failed', 0)
            last_ref = result.get('last_ref', '')
            status = result.get('status', '')
            
            # Update progress bar (will be updated in update_stats)
            
            # Log the vehicle
            if status == 'success':
                self.log(f"[SUCCESS] Downloaded: {last_ref}")
            elif status == 'failure':
                self.log(f"[FAILED] Could not download: {last_ref}")
            
            # Update status
            self.status_label.config(text=f"Processing vehicle {last_ref}...")
        
        elif result_type == 'complete':
            self.log("-" * 60)
            self.log(result.get('message', 'Download complete!'))
            self.log(f"Total processed: {self.processed}")
            self.log(f"Succeeded: {self.succeeded}")
            self.log(f"Failed: {self.failed}")
            
            elapsed = time.time() - self.start_time if self.start_time else 0
            self.log(f"Total time: {format_time(elapsed)}")
            
            self.status_label.config(text="Complete!")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            
            messagebox.showinfo("Complete", 
                              f"Download complete!\n\n"
                              f"Processed: {self.processed}\n"
                              f"Succeeded: {self.succeeded}\n"
                              f"Failed: {self.failed}\n"
                              f"Time: {format_time(elapsed)}")
        
        elif result_type == 'error':
            error_msg = result.get('message', 'Unknown error')
            self.log(f"[ERROR] {error_msg}")
            self.status_label.config(text="Error occurred")
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            
            messagebox.showerror("Error", f"An error occurred:\n\n{error_msg}")
        
        elif result_type == 'stop_requested':
            self.log(result.get('message', 'Stopping...'))
            self.status_label.config(text="Stopping...")
    
    def update_stats(self):
        """Update statistics labels."""
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        
        # Update time elapsed
        self.time_label.config(text=f"Time Elapsed: {format_time(elapsed)}")
        
        # Update speed
        if self.processed > 0:
            speed = calculate_speed(self.processed, elapsed)
            self.speed_label.config(text=f"Speed: {speed:.1f} /hour")
            
            # Update estimated remaining time
            if self.total_items > 0:
                remaining_seconds = estimate_remaining_time(self.processed, self.total_items, elapsed)
                if remaining_seconds >= 0:
                    self.remaining_label.config(text=f"Est. Remaining: {format_time(remaining_seconds)}")
        
        # Update counters
        self.success_label.config(text=f"Succeeded: {self.succeeded}")
        self.failed_label.config(text=f"Failed: {self.failed}")
        
        # Update progress bar and text
        if self.total_items > 0:
            percentage = (self.processed / self.total_items) * 100
            self.progress_bar["value"] = percentage
            self.progress_text.config(text=format_progress(self.processed, self.total_items))
        else:
            # Don't know total yet
            self.progress_text.config(text=f"{self.processed} PDFs downloaded")
        
        # Update again in 1 second if worker is still alive
        if self.worker and self.worker.is_alive():
            self.root.after(1000, self.update_stats)
    
    def log(self, message):
        """
        Add a message to the log.
        
        Args:
            message: Message to log
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def on_closing(self):
        """Handle window close event."""
        if self.worker and self.worker.is_alive():
            if messagebox.askyesno("Confirm Exit", 
                                  "Download is in progress. Are you sure you want to exit?\n\n"
                                  "Progress will be saved and you can resume later."):
                self.worker.stop()
                self.root.destroy()
        else:
            self.root.destroy()

