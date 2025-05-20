import tkinter as tk
import customtkinter as ctk
from tkinter import ttk
import threading


class SoftwareTab:
    def __init__(self, parent, notebook, app):
        self.parent = parent
        self.notebook = notebook
        self.app = app

        # Flag to track if software list has been loaded
        self.loaded = False

        # Create the software tab
        self.create_software_tab()

    def create_software_tab(self):
        """Create the software inventory tab"""
        software_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(software_frame, text="Software")

        # Top section for title and search
        top_section = ctk.CTkFrame(software_frame)
        top_section.pack(fill=tk.X, padx=10, pady=5)

        # Title
        ctk.CTkLabel(
            top_section,
            text="Installed Software",
            font=("Helvetica", 20, "bold")
        ).pack(side=tk.LEFT, padx=10, pady=10)

        # Search frame
        search_frame = ctk.CTkFrame(top_section)
        search_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        ctk.CTkLabel(
            search_frame,
            text="Search:"
        ).pack(side=tk.LEFT, padx=5)

        self.search_entry = ctk.CTkEntry(search_frame, width=200)
        self.search_entry.pack(side=tk.LEFT, padx=5)

        # Add search button
        self.search_button = ctk.CTkButton(
            search_frame,
            text="Search",
            command=self.refresh_software_list
        )
        self.search_button.pack(side=tk.LEFT, padx=5)

        # Add refresh button
        self.refresh_button = ctk.CTkButton(
            search_frame,
            text="↻",
            width=30,
            command=lambda: self.refresh_software_list(clear_search=True)
        )
        self.refresh_button.pack(side=tk.LEFT, padx=5)

        # Status label
        self.status_frame = ctk.CTkFrame(software_frame)
        self.status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Select a computer to view installed software",
            font=("Helvetica", 12)
        )
        self.status_label.pack(pady=5)

        # Create Treeview for software list with columns for Name and Version
        columns = ("name", "version")
        self.software_tree = ttk.Treeview(software_frame, columns=columns, show="headings")

        # Define column headings
        self.software_tree.heading("name", text="Software Name")
        self.software_tree.heading("version", text="Version")

        # Set column widths
        self.software_tree.column("name", width=400)
        self.software_tree.column("version", width=150)

        # Add scrollbars
        scrollbar_y = ttk.Scrollbar(software_frame, orient="vertical", command=self.software_tree.yview)
        scrollbar_x = ttk.Scrollbar(software_frame, orient="horizontal", command=self.software_tree.xview)
        self.software_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        # Pack the treeview and scrollbars
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.software_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar_x.pack(fill=tk.X, padx=10)

        # Bind the tab change event to refresh software list
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_selected)

    def on_tab_selected(self, event):
        """Handle tab selection event"""
        current_tab = self.notebook.select()
        tab_text = self.notebook.tab(current_tab, "text")

        if tab_text == "Software" and not self.loaded and self.app.active_connection:
            # Auto-refresh when tab is selected if a computer is connected
            self.refresh_software_list()

    def refresh_software_list(self, clear_search=False):
        """Refresh the software list from the selected computer"""
        # Clear search if requested
        if clear_search:
            self.search_entry.delete(0, tk.END)

        # Check if a computer is selected
        if not self.app.active_connection:
            self.status_label.configure(text="Please select a computer first")
            return

        # Get search term if any
        search_term = self.search_entry.get().strip()

        # Update status and disable buttons during loading
        self.status_label.configure(text="Loading software inventory...")
        self.search_button.configure(state="disabled")
        self.refresh_button.configure(state="disabled")

        # Clear existing items
        for item in self.software_tree.get_children():
            self.software_tree.delete(item)

        # Start a thread to fetch software inventory
        threading.Thread(target=self._fetch_software_inventory, args=(search_term,), daemon=True).start()

    def _fetch_software_inventory(self, search_term):
        """Fetch software inventory in a separate thread"""
        try:
            # Send request to get software inventory
            response = self.app.connection_manager.send_command(
                self.app.active_connection,
                'software_inventory',
                {'search_term': search_term}
            )

            # Process response on the main thread
            self.app.after(0, lambda: self._process_software_response(response, search_term))

        except Exception as e:
            # Update UI on error
            self.app.after(0, lambda: self._update_status_on_error(str(e)))

    def _process_software_response(self, response, search_term):
        """Process the software inventory response"""
        # Re-enable buttons
        self.search_button.configure(state="normal")
        self.refresh_button.configure(state="normal")

        if not response or response.get('status') != 'success':
            error_msg = response.get('message',
                                     'Failed to retrieve software inventory') if response else "No response from server"
            self.status_label.configure(text=f"Error: {error_msg}")
            return

        # Get software list from response
        software_list = response.get('data', [])

        # Update status with count
        count_text = f"Found {len(software_list)} software"
        if search_term:
            count_text += f" matching '{search_term}'"
        self.status_label.configure(text=count_text)

        # Add software to the tree
        for i, software in enumerate(software_list):
            self.software_tree.insert(
                "",
                tk.END,
                values=(software.get('name', 'Unknown'), software.get('version', 'N/A'))
            )

        # Set loaded flag
        self.loaded = True

    def _update_status_on_error(self, error_msg):
        """Update status label on error"""
        self.status_label.configure(text=f"Error: {error_msg}")
        self.search_button.configure(state="normal")
        self.refresh_button.configure(state="normal")