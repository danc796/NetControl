import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import logging

from nc_client.ui.toast import ToastNotification
from nc_client.ui.monitoring_tab import MonitoringTab
from nc_client.ui.software_tab import SoftwareTab
from nc_client.ui.power_tab import PowerTab
from nc_client.ui.rdp_tab import RDPTab
from nc_client.ui.connection_tab import ConnectionTab

from nc_client.connection.manager import ConnectionManager
from nc_client.monitoring.system_monitor import SystemMonitor
from nc_client.software.inventory import SoftwareManager
from nc_client.power.controller import PowerManager
from nc_client.rdp.client import RDPClient


class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.running = True
        self.active_tab = None
        self.active_connection = None

        self.title("Multi Computers Control")
        self.geometry("1200x800")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Configure logging
        logging.basicConfig(
            filename='nc_client.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

        # Initialize components
        self.toast = ToastNotification(self)
        self.connection_manager = ConnectionManager(self)
        self.system_monitor = SystemMonitor(self)
        self.software_manager = SoftwareManager(self)
        self.power_manager = PowerManager(self)
        self.rdp_client = RDPClient(self)

        # Create UI
        self.create_gui()

        # Set window close handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start monitoring threads
        self.system_monitor.initialize_monitoring()

        # Start connection monitoring
        if hasattr(self.connection_manager, 'initialize_connection_monitoring'):
            self.connection_manager.initialize_connection_monitoring()

    def create_gui(self):
        """Create the main GUI with connection management"""
        # Create main container
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create sidebar
        self.sidebar = ctk.CTkFrame(self.main_container, width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        # Create connection tab in sidebar
        self.connection_tab = ConnectionTab(self.sidebar, self)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_container)
        self.notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create tabs
        self.monitoring_tab = MonitoringTab(self, self.notebook, self)
        self.software_tab = SoftwareTab(self, self.notebook, self)
        self.power_tab = PowerTab(self, self.notebook, self)
        self.rdp_tab = RDPTab(self, self.notebook, self)

        # Add tab change handler
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_change)

    def on_tab_change(self, event=None):
        try:
            current_tab = self.notebook.select()
            prev_tab = self.active_tab
            self.active_tab = self.notebook.tab(current_tab, "text")

            print(f"Tab changed from {prev_tab} to {self.active_tab}")

            # Handle monitoring tab exit
            if prev_tab == "Monitoring":
                self.system_monitor.monitoring_active = False
                print(f"Monitoring deactivated: {self.system_monitor.monitoring_active}")

            # Handle monitoring tab entry
            if self.active_tab == "Monitoring":
                self.system_monitor.monitoring_active = True
                print(f"Monitoring activated: {self.system_monitor.monitoring_active}")

                # Update progress bar references
                if hasattr(self.monitoring_tab, 'cpu_progress'):
                    self.system_monitor.progress_bars['cpu'] = self.monitoring_tab.cpu_progress
                if hasattr(self.monitoring_tab, 'mem_progress'):
                    self.system_monitor.progress_bars['mem'] = self.monitoring_tab.mem_progress

                # Force a refresh
                self.after(100, self.system_monitor.refresh_monitoring)

            # Handle RDP tab activation/deactivation
            if self.active_tab == "Remote Desktop":
                self.rdp_client.rdp_tab_active = True
                print("RDP tab activated")
            else:
                self.rdp_client.rdp_tab_active = False
                print("RDP tab deactivated")

            # Handle software tab entry
            if self.active_tab == "Software":
                self.software_manager.auto_load_software()

            # Update the UI based on the new tab
            self.update_idletasks()

        except Exception as e:
            print(f"Error during tab change: {str(e)}")

    def on_computer_select(self, connection_id):
        """Handle computer selection"""
        if connection_id:
            # Check if active connection is changing
            if self.active_connection != connection_id:
                self.active_connection = connection_id
                # Reset software loaded state when connection changes
                self.software_manager.software_loaded_for = None
                # If software tab is active, load software for new connection
                if self.active_tab == "Software":
                    self.software_manager.auto_load_software()
                # Refresh monitoring for new connection
                self.system_monitor.refresh_monitoring()
        else:
            self.active_connection = None

    def on_closing(self):
        """Handle window closing event"""
        try:
            # Set flag to stop monitoring threads
            self.running = False

            # Close all connections
            self.connection_manager.close_all_connections()

            logging.info("Application shutting down")
            self.quit()

        except Exception as e:
            logging.error(f"Error during shutdown: {str(e)}")
            self.quit()