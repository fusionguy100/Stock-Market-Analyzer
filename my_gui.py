import tkinter as tk
from tkinter import messagebox
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StockMarketApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Market Analyzer by Jacob Newell")

        # Get screen width and set the window width to the screen width and a fixed height
        #screen_width = self.root.winfo_screenwidth()
        self.root.geometry("1200x600")  # Set width to full screen width, height to 400px

        # Input for Stock Ticker
        tk.Label(root, text="Enter Stock Ticker:", font=("Arial", 12)).pack(pady=10)
        self.ticker_entry = tk.Entry(root, font=("Arial", 12))
        self.ticker_entry.pack(pady=5)

        # Fetch Data Button
        self.fetch_button = tk.Button(root, text="Fetch and Analyze", command=self.fetch_data, font=("Arial", 12))
        self.fetch_button.pack(pady=10)

        # Status Label
        self.status_label = tk.Label(root, text="Status: N/A", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Plot Area
        self.plot_frame = tk.Frame(root)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, pady=10)

    def fetch_data(self):
        ticker = self.ticker_entry.get().upper()
        if not ticker:
            messagebox.showerror("Error", "Please enter a valid stock ticker.")
            return

        try:
            # Fetch historical data
            data = yf.download(ticker, period="6mo")
            if data.empty:
                raise ValueError("No data found.")

            # Add Moving Averages
            data["SMA_20"] = data["Close"].rolling(window=20).mean()
            data["SMA_50"] = data["Close"].rolling(window=50).mean()

            # Calculate MACD and Signal Line
            data["EMA_12"] = data["Close"].ewm(span=12, adjust=False).mean()
            data["EMA_26"] = data["Close"].ewm(span=26, adjust=False).mean()
            data["MACD"] = data["EMA_12"] - data["EMA_26"]
            data["Signal_Line"] = data["MACD"].ewm(span=9, adjust=False).mean()

            # Determine Buy or Sell Status
            self.check_buy_sell(data)

            # Plot the data
            self.plot_data(data, ticker)
        except Exception as e:
            messagebox.showerror("Error", f"Could not fetch data: {e}")

    def check_buy_sell(self, data):
        # Check for the "golden cross" (buy) and "death cross" (sell)
        if data["SMA_20"].iloc[-1] > data["SMA_50"].iloc[-1]:
            self.status_label.config(text="Status: Buy", fg="green")  # Buy signal
        elif data["SMA_20"].iloc[-1] < data["SMA_50"].iloc[-1]:
            self.status_label.config(text="Status: Sell", fg="red")  # Sell signal
        else:
            self.status_label.config(text="Status: Hold", fg="orange")  # Hold signal if no cross

    def plot_data(self, data, ticker):
        # Clear previous plots
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        # Create a new figure with two subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), dpi=100)

        # Plot stock prices and SMAs
        ax1.plot(data.index, data["Close"], label="Close Price", color="blue")
        ax1.plot(data.index, data["SMA_20"], label="20-Day SMA", color="orange")
        ax1.plot(data.index, data["SMA_50"], label="50-Day SMA", color="green")
        ax1.set_title(f"{ticker} Stock Analysis")
        ax1.set_ylabel("Price (USD)")
        ax1.legend()

        # Plot MACD and Signal Line
        ax2.plot(data.index, data["MACD"], label="MACD", color="purple")
        ax2.plot(data.index, data["Signal_Line"], label="Signal Line", color="red")
        ax2.bar(data.index, data["MACD"] - data["Signal_Line"], label="MACD Histogram", color="gray", alpha=0.5)
        ax2.set_title("MACD Analysis")
        ax2.set_ylabel("MACD Value")
        ax2.legend()

        # Adjust layout and display the plot in Tkinter
        plt.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = StockMarketApp(root)
    root.mainloop()
