import tkinter as tk
import logging


class SoftwareManager:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.software_loaded_for = None

    def refresh_software_list(self, search_term=""):
        """Refresh software list"""
        if not self.parent_app.active_connection:
            self.update_software_status("Please select a computer first")
            return

        try:
            self.update_software_status("Retrieving software list...")

            # Clear existing items
            for item in self.parent_app.software_tab.software_tree.get_children():
                self.parent_app.software_tab.software_tree.delete(item)

            # Set timeout for software inventory
            connection = self.parent_app.connection_manager.connections.get(self.parent_app.active_connection)
            if not connection:
                self.update_software_status("Connection not found")
                return

            # Set temporary longer timeout
            original_timeout = connection['socket'].gettimeout()
            connection['socket'].settimeout(30)

            try:
                response = self.parent_app.connection_manager.send_command(
                    self.parent_app.active_connection,
                    'software_inventory',
                    {'search': search_term}
                )

                if not response:
                    self.update_software_status("No response from server")
                    return

                if response.get('status') == 'error':
                    self.update_software_status(f"Server error: {response.get('message', 'Unknown error')}")
                    return

                if response.get('status') == 'success':
                    software_list = response.get('data', [])

                    for software in software_list:
                        if isinstance(software, dict):
                            name = software.get('name', 'Unknown')
                            version = software.get('version', 'N/A')

                            self.parent_app.software_tab.software_tree.insert('', 'end', values=(name, version))

                    status = f"Found {len(software_list)} software items"
                    if search_term:
                        status += f" matching '{search_term}'"
                    self.update_software_status(status)
                else:
                    self.update_software_status("Invalid response format")

            finally:
                # Restore original timeout
                connection['socket'].settimeout(original_timeout)

        except Exception as e:
            self.update_software_status(f"Error refreshing list: {str(e)}")

    def update_software_status(self, message):
        """Update status message in software tab"""
        if hasattr(self.parent_app, 'software_tab') and hasattr(self.parent_app.software_tab, 'status_label'):
            self.parent_app.software_tab.status_label.configure(text=message)
        else:
            logging.info(f"Software status: {message}")

    def on_search(self, event=None):
        """Handle software search with case-insensitive matching"""
        if not self.parent_app.active_connection:
            self.update_software_status("Please select a computer first")
            return

        search_term = self.parent_app.software_tab.search_entry.get().strip().lower()  # Convert search term to lowercase

        # Clear the tree
        for item in self.parent_app.software_tab.software_tree.get_children():
            self.parent_app.software_tab.software_tree.delete(item)

        try:
            response = self.parent_app.connection_manager.send_command(
                self.parent_app.active_connection,
                'software_inventory',
                {'search': ''}  # Get all software
            )

            if response and response.get('status') == 'success':
                software_list = response.get('data', [])

                # Filter software list based on search term - case insensitive
                filtered_list = []
                for software in software_list:
                    if isinstance(software, dict):
                        name = software.get('name', '').lower()  # Convert name to lowercase
                        version = software.get('version', '').lower()  # Convert version to lowercase
                        if search_term in name or search_term in version:
                            filtered_list.append(software)

                # Update the tree with filtered results
                for software in filtered_list:
                    self.parent_app.software_tab.software_tree.insert('', 'end', values=(
                        software.get('name', 'Unknown'),
                        software.get('version', 'N/A')
                    ))

                # Update status
                status = f"Found {len(filtered_list)} software items"
                if search_term:
                    status += f" matching '{self.parent_app.software_tab.search_entry.get().strip()}'"  # Show original search term
                self.update_software_status(status)

        except Exception as e:
            self.update_software_status(f"Error during search: {str(e)}")

    def clear_search(self):
        """Clear search and refresh list"""
        self.parent_app.software_tab.search_entry.delete(0, tk.END)
        self.refresh_software_list()  # Refresh with no search term

    def treeview_sort_column(self, col, reverse):
        """Sort treeview column"""
        l = [(self.parent_app.software_tab.software_tree.set(k, col), k) for k in self.parent_app.software_tab.software_tree.get_children('')]
        l.sort(reverse=reverse)

        # Rearrange items in sorted positions
        for index, (val, k) in enumerate(l):
            self.parent_app.software_tab.software_tree.move(k, '', index)

        # Reverse sort next time
        self.parent_app.software_tab.software_tree.heading(col, command=lambda: self.treeview_sort_column(col, not reverse))

    def auto_load_software(self):
        """Automatically load software list if a computer is selected"""
        try:
            # Only load if a computer is connected and it's not already loaded for this connection
            if self.parent_app.active_connection and self.parent_app.active_connection != self.software_loaded_for:
                self.update_software_status("Loading software list...")
                # Schedule software loading with a small delay to allow UI to update
                self.parent_app.after(100, self.refresh_software_list)
                # Update the tracking variable
                self.software_loaded_for = self.parent_app.active_connection
            elif not self.parent_app.active_connection:
                self.update_software_status("Select a computer to view installed software")
        except Exception as e:
            logging.error(f"Error auto-loading software: {str(e)}")