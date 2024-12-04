import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QLabel, QAction, QDialog, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPalette
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pandas as pd
import yfinance as yf
import numpy as np
from PyQt5.QtGui import QIcon


def fetch_live_stock_data(ticker, period="1y"):
    """Fetch live stock data using yfinance."""
    try:
        data = yf.download(ticker, period=period)
        data = data[['Adj Close']]  # Only use Adjusted Close prices
        data.index.name = "date"
        return data
    except Exception as e:
        print(f"Error fetching live data for {ticker}: {e}")
        return None


class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        self.setWindowIcon(QIcon("logo.png"))  # Set the logo for the dialog's title bar

        self.setGeometry(200, 200, 400, 200)
        layout = QVBoxLayout(self)

        about_text = """
        <p>(c) 2024 Peter De Ceuster, SIG Labs<br>
        All Rights Reserved.</p>
        <p><b>Version:</b> SectorFlowAnalyzer v 709.06</p>
        <p><a href='https://buymeacoffee.com/siglabo' style='color:blue; text-decoration:none;'>
        Buy me a coffee</a></p>
          <p><a href='https://peterdeceuster.uk/doc/code-terms' style='color:blue; text-decoration:none;'>
        FPA General Code License</a></p>
        
        """
        about_label = QLabel(about_text, self)
        about_label.setOpenExternalLinks(True)  # Enable clickable links
        layout.addWidget(about_label)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)



class HelpDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Help")
        self.setWindowIcon(QIcon("logo.png"))  # Set the logo for the dialog's title bar

        self.setGeometry(200, 200, 500, 500)

        layout = QVBoxLayout(self)

        help_text = """
        Welcome to the Sector Flow Analyzer!

        This tool helps you analyze sector performance across various market sectors
        like Technology, Consumer Discretionary, Financials, and others, relative to 
        the performance of the S&P 500 index (SPY).

        **Table of Contents:**
        1. Sector ETFs
        2. Relative Performance Calculation
        3. Interpreting the Chart
        4. About Section

        **1. Sector ETFs:**
        - XLK: Technology
        - XLY: Consumer Discretionary
        - XLF: Financials
        - XLI: Industrials
        - XLE: Energy

        **2. Relative Performance Calculation:**
        The 'Performance' is calculated by comparing the cumulative returns of each 
        sector ETF against the S&P 500 (SPY).

        **3. Interpreting the Chart:**
        The chart displays cumulative returns of the selected sectors alongside the 
        benchmark S&P 500. Trends show how each sector fares relative to the index.

        **4. About Section:**
        Check the 'About' menu for licensing and a link to support this project.
        """
        help_label = QLabel(help_text, self)
        help_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(help_label)

        close_button = QPushButton("Close", self)
        close_button.clicked.connect(self.close)
        layout.addWidget(close_button)


class SectorFlowAnalyzerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        
        

        self.setWindowTitle("Sector Flow Analyzer (SFA) v 709.06")
        self.setWindowIcon(QIcon("logo.png"))  # Path to the logo file

        self.setGeometry(100, 100, 900, 700)

        # Set up dark theme
        self.set_theme()

        # Initialize main layout
        self.main_widget = QWidget(self)
        self.layout = QVBoxLayout(self.main_widget)

        # Create menu and widgets
        self.create_menu()
        self.add_widgets()

        self.setCentralWidget(self.main_widget)

        # Initial data fetching and plotting
        self.fetch_data_and_plot()

    def set_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(33, 37, 43))  # Dark gray background
        palette.setColor(QPalette.WindowText, QColor(255, 255, 255))  # White text
        palette.setColor(QPalette.Base, QColor(44, 50, 56))  # Darker gray for table
        palette.setColor(QPalette.AlternateBase, QColor(52, 58, 64))  # Alternate row color
        palette.setColor(QPalette.Text, QColor(255, 255, 255))  # White text in table
        self.setPalette(palette)

    def create_menu(self):
        menu_bar = self.menuBar()

        help_action = QAction("Help", self)
        help_action.triggered.connect(self.show_help_dialog)

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about_dialog)

        menu = menu_bar.addMenu("Help")
        menu.addAction(help_action)
        menu.addAction(about_action)

    def show_help_dialog(self):
        help_dialog = HelpDialog()
        help_dialog.exec_()

    def show_about_dialog(self):
        about_dialog = AboutDialog()
        about_dialog.exec_()

    def fetch_data_and_plot(self):
        sector_tickers = ["XLK", "XLY", "XLF", "XLI", "XLE"]
        sector_names = {
            "XLK": "Technology",
            "XLY": "Consumer Discretionary",
            "XLF": "Financials",
            "XLI": "Industrials",
            "XLE": "Energy",
        }

        print("SFA is now Fetching sector data... Hold on please! (c) SIG 2024")
        sector_data = {
            ticker: fetch_live_stock_data(ticker) for ticker in sector_tickers
        }
        benchmark_data = fetch_live_stock_data("SPY")

        if benchmark_data is None or benchmark_data.empty or any(data is None for data in sector_data.values()):

            print("Error: Unable to fetch all required data.")
            return

        # Align data and calculate performance
        sector_returns = pd.concat(sector_data.values(), axis=1, keys=sector_data.keys()).pct_change().fillna(0)
        benchmark_returns = benchmark_data.pct_change().fillna(0)
        sector_cum_returns = (1 + sector_returns).cumprod()
        benchmark_cum_returns = (1 + benchmark_returns).cumprod()

        relative_performance = sector_cum_returns.sub(benchmark_cum_returns.squeeze(), axis=0)

        self.update_table(sector_cum_returns, relative_performance, sector_names)
        self.plot_sector_performance(sector_cum_returns, benchmark_cum_returns)

    def update_table(self, sector_data, relative_performance, sector_names):
        self.table.setRowCount(len(sector_data.columns))
    
        for i, sector in enumerate(sector_data.columns):
            # Extract ticker for lookup
            ticker = str(sector[0]) if isinstance(sector, tuple) else str(sector)
    
            # Populate table columns
            self.table.setItem(i, 0, QTableWidgetItem(ticker))
            self.table.setItem(i, 1, QTableWidgetItem(sector_names.get(ticker, "Unknown")))
            self.table.setItem(i, 2, QTableWidgetItem(f"{relative_performance[sector].iloc[-1]:.2f}"))
    def plot_sector_performance(self, sector_data, benchmark_data):
        # Create figure and axis
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Custom background color (lighter gray)
        fig.patch.set_facecolor("#f0f0f5")  # Light gray for the entire figure
        ax.set_facecolor("#e6e6e6")  # Slightly darker gray for the plotting area
    
        # Plot sector cumulative returns
        for sector in sector_data.columns:
            ax.plot(
                sector_data.index,
                sector_data[sector],
                label=str(sector[0]) if isinstance(sector, tuple) else str(sector),
                linewidth=2
            )
    
        # Plot benchmark cumulative returns
        ax.plot(
            benchmark_data.index,
            benchmark_data,
            label="S&P 500 (SPY)",
            linestyle="--",
            color="black",
            linewidth=2
        )
    
        # Title and axis labels with darker font
        ax.set_title("Sector Performance vs Benchmark", fontsize=18, color="black")
        ax.set_xlabel("Date", fontsize=14, color="black")
        ax.set_ylabel("Cumulative Returns", fontsize=14, color="black")
    
        # Customize tick parameters for better visibility
        ax.tick_params(colors="black", which="both", labelsize=12)
    
        # Add gridlines with a soft color
        ax.grid(color="white", linestyle="--", linewidth=0.5)
    
        # Add legend with a subtle background
        ax.legend(
            fontsize=12,
            facecolor="white",  # White background for legend
            edgecolor="gray",   # Gray border for legend
            loc="best"
        )
    
        # Embed the plot into the GUI
        canvas = FigureCanvas(fig)
        self.layout.addWidget(canvas)
        canvas.draw()

    def add_widgets(self):
        title = QLabel("Sector Flow Analyzer (SFA) v 709.06", self)
        title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(title)

        self.table = QTableWidget(self)
        self.table.setRowCount(0)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Ticker", "Sector Name", "Relative Performance"])
        self.layout.addWidget(self.table)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SectorFlowAnalyzerGUI()
    window.show()
    window.showMaximized()  # This will make the window start maximized

    sys.exit(app.exec_())
