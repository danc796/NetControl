import tkinter as tk
import customtkinter as ctk
from tkinter import ttk


class SoftwareTab:
    def __init__(self, parent, notebook, app):
        self.parent = parent
        self.notebook = notebook
        self.app = app

        # Create the software tab
        self.create_software_tab()

    def create_software_tab(self):
        """Create the software management tab"""
        self.software_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(self.software_frame, text="Software")

        # Top frame for status and search
        top_frame = ctk.CTkFrame(self.software_frame)
        top_frame.pack(fill=tk.X, padx=10, pady=(5, 0))

        # Status label
        self.status_label = ctk.CTkLabel(
            top_frame,
            text="Select a computer to view installed software"
        )
        self.status_label.pack(side=tk.LEFT, padx=5, pady=5)

        # Search frame
        search_frame = ctk.CTkFrame(top_frame)
        search_frame.pack(side=tk.RIGHT, padx=5, pady=5)

        # Search entry
        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Search software...",
            width=200
        )
        self.search_entry.pack(side=tk.LEFT, padx=(5, 0))

        # Bind search entry to search function
        self.search_entry.bind('<KeyRelease>', self.on_search)

        # Clear search button
        self.clear_search_btn = ctk.CTkButton(
            search_frame,
            text="Clear",
            command=self.clear_search,
            width=60
        )
        self.clear_search_btn.pack(side=tk.LEFT, padx=5)

        # Software list frame
        self.software_list_frame = ctk.CTkFrame(self.software_frame)
        self.software_list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Create and pack the Treeview with scrollbar
        tree_container = ttk.Frame(self.software_list_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create Treeview
        self.software_tree = ttk.Treeview(
            tree_container,
            columns=("Name", "Version"),
            show="headings"
        )

        # Configure columns
        self.software_tree.heading("Name", text="Software Name",
                                   command=lambda: self.treeview_sort_column("Name", False))
        self.software_tree.heading("Version", text="Version",
                                   command=lambda: self.treeview_sort_column("Version", False))

        self.software_tree.column("Name", width=400, minwidth=200)
        self.software_tree.column("Version", width=150, minwidth=100)

        # Create and configure scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self.software_tree.yview)
        self.software_tree.configure(yscrollcommand=scrollbar.set)

        # Pack the tree and scrollbar
        self.software_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Refresh button
        self.refresh_btn = ctk.CTkButton(
            self.software_frame,
            text="Refresh List",
            command=self.refresh_software_list,
            width=120
        )
        self.refresh_btn.pack(pady=5)

    def on_search(self, event=None):
        """Handle software search - delegate to software manager"""
        self.app.software_manager.on_search(self.search_entry.get().strip())

    def clear_search(self):
        """Clear search and refresh list"""
        self.search_entry.delete(0, tk.END)
        self.refresh_software_list()

    def refresh_software_list(self):
        """Refresh software list"""
        self.app.software_manager.refresh_software_list()

    def treeview_sort_column(self, col, reverse):
        """Sort treeview column - delegate to software manager"""
        self.app.software_manager.treeview_sort_column(col, reverse)