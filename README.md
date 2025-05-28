# Stock Market Analyzer

**Interactive Desktop App** for fetching, analyzing, and visualizing stock price data with technical indicators and trade signals.

---

## 📌 Features

* **Real-time Data**: Pulls historical and live data via the [yfinance](https://pypi.org/project/yfinance/) API.
* **Price Chart**: Candlestick plotting with configurable 20- & 50-day Simple Moving Averages (SMA).
* **MACD Panel**: Displays MACD, Signal line, and histogram in a dedicated sub-chart.
* **RSI Overlay (Optional)**: Relative Strength Index panel with overbought (70) and oversold (30) thresholds.
* **Bollinger Bands (Optional)**: Upper and lower bands overlaid on the price chart.
* **Buy/Sell Signals**:

  * **SMA Crossover** LED indicator
  * **MACD Signal** LED indicator
  * **RSI** and **BB Squeeze** status LEDs when enabled
* **Export & Save**:

  * Save chart as **PNG**
  * Export raw data to **CSV**/**Excel**
* **Interactive UI**:

  * Dark/light theme toggle
  * Timeframe selector (1mo, 3mo, 6mo, 1y)
  * Panning/zooming with toolbar
  * Hover tooltips for exact values

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.8+**
* **pip** package manager

### Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/fusionguy100/Stock-Market-Analyzer.git
   cd Stock-Market-Analyzer
   ```
2. **Create & activate a virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # macOS/Linux
   .\.venv\Scripts\activate     # Windows
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

### Dependencies

* `customtkinter` for modern UI widgets
* `yfinance` for data fetching
* `mplfinance` & `matplotlib` for charting
* `pandas` & `numpy` for data processing

Refer to `requirements.txt` for full version details.

---

## 🖥️ Usage

1. **Run the application**:

   ```bash
   python my_gui.py
   ```
2. **Enter a ticker symbol** (e.g. `AAPL`, `TSLA`)
3. **Select timeframe** from the dropdown (e.g., 6mo)
4. **Click** **Fetch & Analyze**
5. **Toggle** optional overlays under **Indicators** menu (RSI, Bollinger Bands)
6. **Save** chart or **Export** data via the **File** menu.

---

## 📸 Screenshots

![Price & MACD Chart](assets/stock_app_demo.png)

---

## 🛠️ Development

* Follow the existing code structure in `my_gui.py`.
* UI is built with **CustomTkinter**.
* Charting is handled by **mplfinance** with dynamic `addplot` panels.

## 📄 License

MIT © Jacob Newell

---

*Created by Jacob Newell – [fusionguy100](https://github.com/fusionguy100)*
