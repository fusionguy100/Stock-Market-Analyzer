import os
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox
import tkinter.ttk as ttk
import customtkinter as ctk
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.lines import Line2D
import mplcursors
from datetime import datetime
import numpy as np

# Suppress benign mplcursors warnings
warnings.filterwarnings(
    "ignore",
    message="Pick support for PolyCollection is missing",
    category=UserWarning
)

# Configure theme defaults
ctk.set_appearance_mode("dark")  # user can toggle in Settings
ctk.set_default_color_theme("dark-blue")

class StockMarketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Market Analyzer by Jacob Newell")
        self.root.geometry("1200x700")
        self.root.protocol("WM_DELETE_WINDOW", self.on_exit)

        # Grid configuration
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # Menu
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Chart", command=self.save_chart)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="File", menu=file_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="Toggle Theme", command=self.toggle_theme)
        menubar.add_cascade(label="Settings", menu=settings_menu)

        indicator_menu = tk.Menu(menubar, tearoff=0)
        self.rsi_var = tk.BooleanVar(value=False)
        self.bb_var = tk.BooleanVar(value=False)
        indicator_menu.add_checkbutton(label="RSI", variable=self.rsi_var, command=self.toggle_rsi)
        indicator_menu.add_checkbutton(label="Bollinger Bands", variable=self.bb_var, command=self.toggle_bb)
        menubar.add_cascade(label="Indicators", menu=indicator_menu)

        self.root.config(menu=menubar)

        # Timeframe/Interval frame
        top_frame = ctk.CTkFrame(self.root)
        top_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        top_frame.grid_columnconfigure((1,3), weight=1)
        ctk.CTkLabel(top_frame, text="Interval:").grid(row=0, column=0, padx=5)
        self.period = "6mo"
        self.interval_cb = ctk.CTkComboBox(
            top_frame,
            values=["1mo","3mo","6mo","1y"],
            command=lambda v: setattr(self, 'period', v)
        )
        self.interval_cb.set(self.period)
        self.interval_cb.grid(row=0, column=1, padx=5, sticky="ew")

        ctk.CTkLabel(top_frame, text="Ticker:").grid(row=0, column=2, padx=5)
        self.ticker_entry = ctk.CTkEntry(top_frame, placeholder_text="e.g. AAPL")
        self.ticker_entry.grid(row=0, column=3, padx=5, sticky="ew")

        self.fetch_button = ctk.CTkButton(top_frame, text="Fetch & Analyze", command=self.fetch_data)
        self.fetch_button.grid(row=0, column=4, padx=5)

        # Input panel for status
        self.input_frame = ctk.CTkFrame(self.root, width=200)
        self.input_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        self.input_frame.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.input_frame, text="Status Panel", font=(None,16)).pack(pady=(5,10))
        self.status_vars = {}
        for name in ["SMA Crossover","RSI OB/OS","BB Squeeze","MACD Signal"]:
            lbl = ctk.CTkLabel(self.input_frame, text=f"{name}:", anchor="w")
            led = ctk.CTkLabel(self.input_frame, text="●", font=(None,18), text_color="grey")
            lbl.pack(fill="x", padx=10, pady=(5,0))
            led.pack(padx=10)
            self.status_vars[name] = led

        # Plot container
        self.plot_container = tk.Frame(self.root)
        self.plot_container.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.plot_container.grid_rowconfigure(0, weight=1)
        self.plot_container.grid_columnconfigure(0, weight=1)

        # Inner frames for canvas and toolbar
        self.chart_frame = tk.Frame(self.plot_container)
        self.chart_frame.grid(row=0, column=0, sticky='nsew')
        self.toolbar_frame = tk.Frame(self.plot_container)
        self.toolbar_frame.grid(row=1, column=0, sticky='ew')

        self.canvas = None
        self.toolbar = None

        # Feature toggles
        self.show_rsi = False
        self.show_bb = False

        # Data storage
        self.latest_df = None

    def fetch_data(self):
        ticker = self.ticker_entry.get().strip().upper().lstrip('$')
        if not ticker:
            messagebox.showerror("Error","Please enter a ticker.")
            return
        try:
            df = yf.Ticker(ticker).history(period=self.period)
        except Exception as e:
            messagebox.showerror("Error",f"Download failed: {e}")
            return
        if df.empty:
            messagebox.showerror("Error","No data retrieved.")
            return

        # Compute indicators
        df['SMA20'] = df['Close'].rolling(20).mean()
        df['SMA50'] = df['Close'].rolling(50).mean()
        # MACD
        df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = df['EMA12'] - df['EMA26']
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        # RSI and BB
        if self.show_rsi:
            delta = df['Close'].diff()
            up = delta.clip(lower=0); down = -delta.clip(upper=0)
            ma_up = up.rolling(14).mean(); ma_down = down.rolling(14).mean()
            rs = ma_up/ma_down; df['RSI'] = 100 - (100/(1+rs))
        if self.show_bb:
            sma = df['Close'].rolling(20).mean()
            std = df['Close'].rolling(20).std()
            df['BB_up'] = sma + 2*std
            df['BB_dn'] = sma - 2*std

        # Drop only where SMA20/SMA50 or MACD/Signal NaN
        df_plot = df.dropna(subset=['SMA20','SMA50','MACD','Signal'])
        if df_plot.empty:
            messagebox.showerror("Error","Not enough data for indicators.")
            return

        self.latest_df = df
        self.update_status(df_plot)
        self.plot(df_plot)

    def update_status(self, df):
        # SMA
        led = self.status_vars['SMA Crossover']
        led.configure(text_color=("green" if df['SMA20'].iloc[-1] > df['SMA50'].iloc[-1] else "red"))
        # RSI
        if self.show_rsi and 'RSI' in df.columns:
            rsi = df['RSI'].iloc[-1]
            led = self.status_vars['RSI OB/OS']
            color = 'green' if rsi < 30 else 'red' if rsi > 70 else 'orange'
            led.configure(text_color=color)
        # BB squeeze
        if self.show_bb and 'BB_up' in df.columns:
            width = df['BB_up'].iloc[-1] - df['BB_dn'].iloc[-1]
            led = self.status_vars['BB Squeeze']
            led.configure(text_color=("green" if width > df['Close'].std()*0.1 else "orange"))
        # MACD Signal line crossover
        led = self.status_vars['MACD Signal']
        color = 'green' if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] else 'red'
        led.configure(text_color=color)

    def plot(self, df):
        # clear previous widgets
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        for widget in self.toolbar_frame.winfo_children():
            widget.destroy()

        # Prepare additional plots (MACD, RSI, BB)
        addplots = []
        # MACD panel
        addplots.extend([
            mpf.make_addplot(df['MACD'], panel=1, color='blue', ylabel='MACD'),
            mpf.make_addplot(df['Signal'], panel=1, color='orange'),
            mpf.make_addplot(df['MACD'] - df['Signal'], type='bar', panel=1, alpha=0.5)
        ])
        # RSI panel if enabled
        if self.show_rsi and 'RSI' in df.columns:
            addplots.append(mpf.make_addplot(df['RSI'], panel=2, color='purple', ylabel='RSI', secondary_y=False))
        # Bollinger Bands overlay
        if self.show_bb and 'BB_up' in df.columns:
            addplots.append(mpf.make_addplot(df['BB_up'], panel=0, color='grey', linestyle='--'))
            addplots.append(mpf.make_addplot(df['BB_dn'], panel=0, color='grey', linestyle='--'))

        # Plot using mplfinance with panels: price, MACD, (RSI), volume
        panels = 3 if self.show_rsi else 2
        panel_ratios = (3,1,1) if self.show_rsi else (4,1)
        fig, axes = mpf.plot(
            df,
            type='candle',
            mav=(20,50),
            volume=True,
            addplot=addplots,
            panel_ratios=panel_ratios,
            style='charles',
            returnfig=True,
            figsize=(10,6)
        )

        # Embed figure in Tkinter
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)

        # Navigation toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        self.toolbar.update()
        self.toolbar.pack(fill='x')

        # Tooltips on line plots
        for ax in fig.axes:
            lines = [line for line in ax.get_lines() if isinstance(line, Line2D)]
            if lines:
                mplcursors.cursor(lines, hover=True)

    def save_chart(self):
        if self.latest_df is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[('PNG','*.png')])
        if path:
            self.canvas.figure.savefig(path)

    def export_data(self):
        if self.latest_df is None:
            return
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV','*.csv'),('Excel','*.xlsx')])
        if path.endswith('.csv'):
            self.latest_df.to_csv(path)
        else:
            self.latest_df.to_excel(path)

    def toggle_theme(self):
        mode = "light" if ctk.get_appearance_mode() == "dark" else "dark"
        ctk.set_appearance_mode(mode)

    def toggle_rsi(self):
        self.show_rsi = self.rsi_var.get()
        if self.latest_df is not None:
            df_plot = self.latest_df.dropna(subset=['SMA20','SMA50','MACD','Signal'])
            self.update_status(df_plot)
            self.plot(df_plot)

    def toggle_bb(self):
        self.show_bb = self.bb_var.get()
        if self.latest_df is not None:
            df_plot = self.latest_df.dropna(subset=['SMA20','SMA50','MACD','Signal'])
            self.update_status(df_plot)
            self.plot(df_plot)

    def on_exit(self):
        self.root.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = StockMarketApp(root)
    root.mainloop()
