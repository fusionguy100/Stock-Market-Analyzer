import os
import warnings
import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
import customtkinter as ctk
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.lines import Line2D
import mplcursors
from datetime import datetime

# Suppress benign mplcursors warnings
warnings.filterwarnings(
    "ignore",
    message="Pick support for PolyCollection is missing",
    category=UserWarning
)

# Configure theme
ctk.set_appearance_mode("dark")  # "light" or "dark"
ctk.set_default_color_theme("dark-blue")  # Themes: dark-blue, light-blue, green

class StockMarketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Market Analyzer by Jacob Newell")
        self.root.geometry("1200x600")
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Grid configuration
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Menu
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Chart", command=self.save_chart)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

        # Input panel
        self.input_frame = ctk.CTkFrame(self.root, width=300, corner_radius=10)
        self.input_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.input_frame.grid_rowconfigure(6, weight=1)

        ctk.CTkLabel(self.input_frame, text="Enter Stock Ticker:", font=(None, 14))\
            .grid(row=0, column=0, padx=10, pady=(20,5), sticky="w")
        self.ticker_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g. AAPL", font=(None, 14))
        self.ticker_entry.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.fetch_button = ctk.CTkButton(self.input_frame, text="Fetch & Analyze", command=self.fetch_data)
        self.fetch_button.grid(row=2, column=0, padx=10, pady=(10,5))

        self.led_label = ctk.CTkLabel(self.input_frame, text="●", font=(None, 24), text_color="grey")
        self.led_label.grid(row=3, column=0, pady=(10,0))
        self.status_text = ctk.CTkLabel(self.input_frame, text="Status: N/A", font=(None, 12))
        self.status_text.grid(row=4, column=0, pady=(5,10))

        self.loader = ttk.Progressbar(self.input_frame, mode='indeterminate')

        # Plot area
        self.plot_frame = ctk.CTkFrame(self.root, corner_radius=10)
        self.plot_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.plot_frame.grid_rowconfigure(0, weight=1)
        self.plot_frame.grid_columnconfigure(0, weight=1)

        self.current_fig = None

    def fetch_data(self):
        ticker = self.ticker_entry.get().strip().upper()
        if not ticker:
            messagebox.showerror("Error", "Please enter a valid stock ticker.")
            return

        self.loader.grid(row=5, column=0, padx=10, pady=(10,0), sticky="ew")
        self.loader.start()
        self.root.update_idletasks()

        try:
            df = yf.Ticker(ticker).history(period="6mo")
        except Exception as e:
            self._stop_loader()
            messagebox.showerror("Error", f"Download failed: {e}")
            return

        if df.empty:
            self._stop_loader()
            messagebox.showerror("Error", f"No data for ticker {ticker}.")
            return

        required = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing = [c for c in required if c not in df.columns]
        if missing:
            self._stop_loader()
            messagebox.showerror("Error", f"Missing columns: {', '.join(missing)}")
            return

        try:
            df[required] = df[required].apply(pd.to_numeric, errors='coerce')
            df.dropna(subset=required, inplace=True)
            df['SMA20'] = df['Close'].rolling(20).mean()
            df['SMA50'] = df['Close'].rolling(50).mean()
        except Exception as e:
            self._stop_loader()
            messagebox.showerror("Error", f"Processing error: {e}")
            return

        self._update_status(df)
        self._plot(df, ticker)
        self._stop_loader()

    def _stop_loader(self):
        self.loader.stop()
        self.loader.grid_remove()

    def _update_status(self, df):
        if df['SMA20'].iloc[-1] > df['SMA50'].iloc[-1]:
            self.led_label.configure(text_color="green")
            self.status_text.configure(text="Status: Buy")
        elif df['SMA20'].iloc[-1] < df['SMA50'].iloc[-1]:
            self.led_label.configure(text_color="red")
            self.status_text.configure(text="Status: Sell")
        else:
            self.led_label.configure(text_color="orange")
            self.status_text.configure(text="Status: Hold")

    def _plot(self, df, ticker):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        df2 = df.dropna(subset=['SMA20', 'SMA50'])
        fig, axes = mpf.plot(
            df2, type='candle', mav=(20,50), volume=True,
            style='charles', returnfig=True, figsize=(8,6)
        )
        self.current_fig = fig

        # Attach tooltip only to line artists
        for ax in axes:
            lines = [artist for artist in ax.get_children() if isinstance(artist, Line2D)]
            if lines:
                mplcursors.cursor(lines, hover=True)

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

    def save_chart(self):
        if not self.current_fig:
            messagebox.showerror("Error", "No chart to save.")
            return
        save_dir = os.path.join(os.getcwd(), 'charts')
        os.makedirs(save_dir, exist_ok=True)
        fname = f"{self.ticker_entry.get().upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        self.current_fig.savefig(os.path.join(save_dir, fname))
        messagebox.showinfo("Saved", f"Chart saved to {save_dir}/{fname}")

    def on_exit(self):
        # Graceful exit to cancel pending callbacks
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StockMarketApp(root)
    try:
        root.mainloop()
    except tk.TclError:
        pass
