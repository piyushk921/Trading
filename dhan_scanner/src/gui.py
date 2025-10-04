# src/gui.py

import tkinter as tk
from tkinter import ttk, scrolledtext
import queue
import threading
from datetime import datetime, timedelta

from .scanner import Scanner
from .config import get_scanner_config

class ScannerGUI:
    """
    The main GUI for the Dhan Option Chain Scanner.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("Dhan Intraday Option Scanner")
        self.root.geometry("950x650")

        # --- State Variables ---
        self.scanner = None
        self.is_running = False
        self.scan_interval_minutes = get_scanner_config().get("scan_interval_minutes", 5)
        self.next_scan_time = None

        # --- Communication Queue ---
        self.gui_queue = queue.Queue()

        # --- UI Setup ---
        # A dictionary to hold the Treeview widgets for easy access
        self.signal_trees = {}
        self._setup_widgets()
        self._center_window()

        # Start the queue processor and countdown timer
        self.root.after(100, self.process_queue)
        self.root.after(1000, self.update_countdown)

    def _setup_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # --- Control Buttons ---
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        self.start_button = ttk.Button(control_frame, text="Start Scanner", command=self.start_scanner)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(control_frame, text="Stop Scanner", command=self.stop_scanner, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        # --- Signal Notebook (Tabs) ---
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)

        # Create the four tabs for the different signal types
        self._create_signal_tab(notebook, "Long Unwinding", "Longs (CE Unwind)")
        self._create_signal_tab(notebook, "Short Unwinding", "Shorts (PE Unwind)")
        self._create_signal_tab(notebook, "CE Buildup", "CE Buildup")
        self._create_signal_tab(notebook, "PE Buildup", "PE Buildup")

        # --- Log Panel ---
        log_frame = ttk.LabelFrame(main_frame, text="Logs", height=150)
        log_frame.pack(fill=tk.X, pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # --- Status Bar ---
        self.status_bar = ttk.Label(self.root, text="Status: Idle", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.countdown_label = ttk.Label(self.status_bar, text="Next Scan: --:--")
        self.countdown_label.pack(side=tk.RIGHT, padx=10)

    def _create_signal_tab(self, parent_notebook, signal_key, tab_title):
        """Creates a tab with a Treeview for displaying signals."""
        frame = ttk.Frame(parent_notebook, padding=5)
        parent_notebook.add(frame, text=tab_title)

        columns = ("symbol", "ltp", "strike", "threshold", "ce_oi_chg", "pe_oi_chg", "time")
        tree = ttk.Treeview(frame, columns=columns, show="headings")

        tree.heading("symbol", text="Symbol")
        tree.heading("ltp", text="LTP")
        tree.heading("strike", text="Trigger Strike")
        tree.heading("threshold", text="Threshold")
        tree.heading("ce_oi_chg", text="CE ΔOI %")
        tree.heading("pe_oi_chg", text="PE ΔOI %")
        tree.heading("time", text="Time")

        tree.column("symbol", width=100)
        tree.column("ltp", width=80)
        tree.column("strike", width=100)
        tree.column("threshold", width=80, anchor=tk.CENTER)
        tree.column("ce_oi_chg", width=100, anchor=tk.E)
        tree.column("pe_oi_chg", width=100, anchor=tk.E)
        tree.column("time", width=100)

        tree.pack(fill=tk.BOTH, expand=True)
        self.signal_trees[signal_key] = tree

    def _center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def start_scanner(self):
        # Clear all previous signals from the lists when starting a new session
        for tree in self.signal_trees.values():
            tree.delete(*tree.get_children())

        try:
            self.scanner = Scanner(self.gui_queue)
            self.scanner.start()
            # The start method now returns immediately or not at all if health check fails
            if self.scanner.running:
                self.is_running = True
                self.start_button.config(state=tk.DISABLED)
                self.stop_button.config(state=tk.NORMAL)
                self.update_status("Scanner running...")
                self.reset_countdown()
        except Exception as e:
            self.log_message("CRITICAL", f"Failed to initialize scanner: {e}")
            self.update_status(f"Error: {e}")

    def stop_scanner(self):
        if self.scanner:
            self.scanner.stop()
            self.scanner = None
        self.is_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Scanner stopped.")
        self.next_scan_time = None

    def update_status(self, text):
        self.status_bar.config(text=f"Status: {text}")

    def log_message(self, level, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] [{level}] {message}\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)

        if "Starting new scan cycle" in message:
            self.reset_countdown()

    def reset_countdown(self):
        self.next_scan_time = datetime.now() + timedelta(minutes=self.scan_interval_minutes)

    def update_countdown(self):
        if self.is_running and self.next_scan_time:
            remaining = self.next_scan_time - datetime.now()
            if remaining.total_seconds() > 0:
                mins, secs = divmod(int(remaining.total_seconds()), 60)
                self.countdown_label.config(text=f"Next Scan: {mins:02d}:{secs:02d}")
            else:
                self.countdown_label.config(text="Next Scan: Now...")
        else:
            self.countdown_label.config(text="Next Scan: --:--")

        self.root.after(1000, self.update_countdown)

    def add_signal_to_list(self, signal_data):
        signal_type = signal_data["signal_type"]

        # Get the correct tree view from our dictionary
        tree = self.signal_trees.get(signal_type)
        if not tree:
            self.log_message("ERROR", f"GUI received unknown signal type: {signal_type}")
            return

        values = (
            signal_data["symbol"],
            f"{signal_data['ltp']:.2f}",
            signal_data["strike"],
            f"> {signal_data['threshold']}%", # Format the threshold
            f"{signal_data['ce_change']:.2f}%",
            f"{signal_data['pe_change']:.2f}%",
            datetime.now().strftime("%H:%M:%S")
        )
        tree.insert("", tk.END, values=values)

    def process_queue(self):
        try:
            while True:
                message = self.gui_queue.get_nowait()

                if isinstance(message, str) and message.startswith("LOG:"):
                    _, level, msg = message.split(":", 2)
                    self.log_message(level, msg)
                    if "Scanner stopped" in msg:
                        self.update_status("Idle")

                elif isinstance(message, dict) and message.get("type") == "SIGNAL":
                    self.add_signal_to_list(message)

        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def on_closing(self):
        if self.is_running:
            self.stop_scanner()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ScannerGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()