import tkinter as tk, messagebox
import customtkinter as ctk
import logging


class CentralServerTab:
    def __init__(self, parent, notebook, app):
        self.parent = parent
        self.notebook = notebook
        self.app = app

        # Create the central server tab
        self.create_central_server_tab()

    def create_central_server_tab(self):
        """Create the central server tab"""
        central_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(central_frame, text="Central Server")

        # Title
        title_label = ctk.CTkLabel(
            central_frame,
            text="Central Server Connection",
            font=("Helvetica", 20, "bold")
        )
        title_label.pack(pady=(20, 10))

        # Status section
        self.status_frame = ctk.CTkFrame(central_frame)
        self.status_frame.pack(fill=tk.X, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text=f"Connected as {self.app.central_client.username}",
            font=("Helvetica", 14),
            text_color="#00CC00"
        )
        self.status_label.pack(pady=10)

        # Connection details
        self.details_label = ctk.CTkLabel(
            self.status_frame,
            text=f"Server: {self.app.central_client.host}:{self.app.central_client.port}",
            font=("Helvetica", 12)
        )
        self.details_label.pack(pady=5)

        # Logout button
        self.logout_button = ctk.CTkButton(
            self.status_frame,
            text="Logout",
            command=self.logout,
            width=150,
            height=30
        )
        self.logout_button.pack(pady=10)

        # Server actions
        actions_frame = ctk.CTkFrame(central_frame)
        actions_frame.pack(fill=tk.X, padx=20, pady=(20, 10))

        # Shared servers
        shared_servers_frame = ctk.CTkFrame(actions_frame)
        shared_servers_frame.pack(fill=tk.X, pady=10)

        ctk.CTkLabel(
            shared_servers_frame,
            text="Shared Servers",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(10, 5))

        self.shared_servers_label = ctk.CTkLabel(
            shared_servers_frame,
            text="No shared servers available"
        )
        self.shared_servers_label.pack(pady=5)

        self.connect_shared_button = ctk.CTkButton(
            shared_servers_frame,
            text="Connect to Shared Servers",
            command=self.connect_to_shared_servers,
            width=200,
            height=40
        )
        self.connect_shared_button.pack(pady=10)

        # Admin section - make it more visible and ensure it appears
        # Create an admin section container
        admin_container = ctk.CTkFrame(central_frame)
        admin_container.pack(fill=tk.X, padx=20, pady=(20, 10), expand=True)

        # Store reference to the container
        self.admin_container = admin_container

        # Create the admin frame inside the container
        self.admin_frame = ctk.CTkFrame(admin_container)
        # Don't pack it yet - we'll do that in update_ui based on admin status

        ctk.CTkLabel(
            self.admin_frame,
            text="Admin Functions",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(10, 5))

        # User creation form
        user_creation_frame = ctk.CTkFrame(self.admin_frame)
        user_creation_frame.pack(fill=tk.X, pady=5)

        ctk.CTkLabel(user_creation_frame, text="Create New User", font=("Helvetica", 14)).pack(pady=(5, 2))

        form_frame = ctk.CTkFrame(user_creation_frame)
        form_frame.pack(pady=5)

        ctk.CTkLabel(form_frame, text="Username:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.new_username_entry = ctk.CTkEntry(form_frame, placeholder_text="New Username", width=200)
        self.new_username_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(form_frame, text="Password:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.new_password_entry = ctk.CTkEntry(form_frame, placeholder_text="New Password", show="*", width=200)
        self.new_password_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        self.is_admin_var = tk.BooleanVar(value=False)
        self.is_admin_checkbox = ctk.CTkCheckBox(form_frame, text="Make Admin", variable=self.is_admin_var)
        self.is_admin_checkbox.grid(row=2, column=0, columnspan=2, padx=10, pady=5)

        ctk.CTkButton(
            form_frame,
            text="Create User",
            command=self.create_user,
            width=150
        ).grid(row=3, column=0, columnspan=2, padx=10, pady=10)

        # Update UI periodically
        self.update_ui()

    def logout(self):
        """Handle logout by completely restarting the application"""
        if self.app.central_client.authenticated:
            if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out? The application will restart."):
                # Disconnect from central server
                self.app.central_client.disconnect()

                # Log the restart
                logging.info("Restarting application after logout...")

                # Start the full restart process
                self.restart_application()

    def restart_application(self):
        """Completely restart the application without visible command prompts"""
        try:
            # Set flag to stop monitoring threads
            self.app.running = False

            # Close all connections
            self.app.connection_manager.close_all_connections()

            # Use subprocess.Popen with hidden window
            import sys
            import os
            import subprocess

            # Get the current executable path and arguments
            if getattr(sys, 'frozen', False):
                # If running as an executable
                executable = sys.executable
                args = []
            else:
                # If running as a script
                executable = sys.executable
                args = [os.path.abspath(sys.argv[0])]

            # Create a detached/hidden process based on platform
            if sys.platform.startswith('win'):
                # For Windows - use DETACHED_PROCESS flag to hide the window
                import ctypes

                # Create a proper startupinfo object to hide the window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE

                # Use DETACHED_PROCESS flag
                DETACHED_PROCESS = 0x00000008

                # Start the new process
                subprocess.Popen(
                    [executable] + args,
                    creationflags=DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
                    startupinfo=startupinfo,
                    close_fds=True
                )
            else:
                # For Unix-like systems
                subprocess.Popen(
                    [executable] + args,
                    start_new_session=True,
                    close_fds=True
                )

            # Give the new process a moment to start
            import time
            time.sleep(0.5)

            # Now exit the application
            self.app.destroy()

            # Force a complete exit
            os._exit(0)

        except Exception as e:
            logging.error(f"Error during application restart: {e}")
            messagebox.showerror("Restart Error", f"Failed to restart: {str(e)}")

            # Fall back to the original restart method as a last resort
            self.app.restart_application()

    def connect_to_shared_servers(self):
        """Connect to all shared servers"""
        self.app.connect_to_shared_servers()

    def update_ui(self):
        """Update UI elements periodically"""
        # Update status label with current username
        if self.app.central_client.authenticated and self.app.central_client.username:
            self.status_label.configure(
                text=f"Connected as {self.app.central_client.username}",
                text_color="#00CC00"
            )

            # Update server details
            self.details_label.configure(
                text=f"Server: {self.app.central_client.host}:{self.app.central_client.port}"
            )
        else:
            self.status_label.configure(
                text="Not connected",
                text_color="#FFFFFF"
            )
            self.details_label.configure(text="")

        # Update shared servers label if connected to central server
        if self.app.central_client.authenticated:
            self.update_shared_servers_label()

        # Show/hide admin panel with better visibility control
        if self.app.central_client.authenticated and self.app.central_client.is_admin:
            # Make sure admin frame is packed in its container
            self.admin_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Add a visual indicator that admin mode is active
            self.admin_container.configure(border_width=2, border_color="#00CC00")
        else:
            # Unpack if it was previously packed
            self.admin_frame.pack_forget()

            # Remove border if not admin
            self.admin_container.configure(border_width=0)

        # Schedule next update
        self.app.after(2000, self.update_ui)

    def update_shared_servers_label(self):
        """Update shared servers label with count of available shared servers"""
        if not self.app.central_client.authenticated:
            return

        # Refresh server lists
        self.app.central_client.refresh_server_lists()

        # Update label
        count = len(self.app.central_client.shared_servers)
        if count > 0:
            self.shared_servers_label.configure(
                text=f"{count} shared servers available"
            )
        else:
            self.shared_servers_label.configure(
                text="No shared servers available"
            )

    def create_user(self):
        """Handle creating a new user"""
        username = self.new_username_entry.get()
        password = self.new_password_entry.get()
        is_admin = self.is_admin_var.get()

        if not username or not password:
            self.app.toast.show_toast("Please provide username and password", "warning")
            return

        success, message = self.app.central_client.create_user(username, password, is_admin)

        if success:
            self.app.toast.show_toast(message, "success")
            self.new_username_entry.delete(0, 'end')
            self.new_password_entry.delete(0, 'end')
            self.is_admin_var.set(False)
        else:
            self.app.toast.show_toast(message, "error")