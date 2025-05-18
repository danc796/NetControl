import tkinter as tk
import customtkinter as ctk


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

        # Login status
        self.status_frame = ctk.CTkFrame(central_frame)
        self.status_frame.pack(fill=tk.X, padx=20, pady=10)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Not connected",
            font=("Helvetica", 14)
        )
        self.status_label.pack(pady=10)

        # Login form
        login_frame = ctk.CTkFrame(central_frame)
        login_frame.pack(fill=tk.X, padx=20, pady=10)

        # Connection info
        connection_frame = ctk.CTkFrame(login_frame)
        connection_frame.pack(fill=tk.X, pady=5)

        ctk.CTkLabel(connection_frame, text="Server:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.host_entry = ctk.CTkEntry(connection_frame, placeholder_text="IP Address", width=200)
        self.host_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(connection_frame, text="Port:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.port_entry = ctk.CTkEntry(connection_frame, placeholder_text="5001", width=200)
        self.port_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        self.port_entry.insert(0, "5001")

        # Username/password
        auth_frame = ctk.CTkFrame(login_frame)
        auth_frame.pack(fill=tk.X, pady=5)

        ctk.CTkLabel(auth_frame, text="Username:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.username_entry = ctk.CTkEntry(auth_frame, placeholder_text="Username", width=200)
        self.username_entry.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(auth_frame, text="Password:").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.password_entry = ctk.CTkEntry(auth_frame, placeholder_text="Password", show="*", width=200)
        self.password_entry.grid(row=1, column=1, padx=10, pady=5, sticky="w")

        # Login button
        button_frame = ctk.CTkFrame(login_frame)
        button_frame.pack(fill=tk.X, pady=10)

        self.login_button = ctk.CTkButton(
            button_frame,
            text="Login",
            command=self.login,
            width=150,
            height=40
        )
        self.login_button.pack(pady=10)

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
            state="disabled",
            width=200,
            height=40
        )
        self.connect_shared_button.pack(pady=10)

        # Sharing controls
        sharing_frame = ctk.CTkFrame(actions_frame)
        sharing_frame.pack(fill=tk.X, pady=10)

        ctk.CTkLabel(
            sharing_frame,
            text="Connection Sharing",
            font=("Helvetica", 16, "bold")
        ).pack(pady=(10, 5))

        # Show currently active connection
        self.active_conn_label = ctk.CTkLabel(
            sharing_frame,
            text="No active connection"
        )
        self.active_conn_label.pack(pady=5)

        # Sharing toggle button
        self.sharing_button = ctk.CTkButton(
            sharing_frame,
            text="Enable Sharing",
            command=self.toggle_sharing,
            state="disabled",
            width=200,
            height=40
        )
        self.sharing_button.pack(pady=10)

        # admin section
        self.admin_frame = ctk.CTkFrame(central_frame)
        self.admin_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        self.admin_frame.pack_forget()  # Hide by default

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

    def login(self):
        """Handle login button click"""
        host = self.host_entry.get()
        port = self.port_entry.get() or "5001"
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not host or not username or not password:
            self.app.toast.show_toast("Please fill in all fields", "warning")
            return

        # Try to connect
        try:
            port = int(port)
        except ValueError:
            self.app.toast.show_toast("Invalid port number", "error")
            return

        # Connect to central server
        if self.app.connect_to_central_server(host, port, username, password):
            # Update UI
            self.status_label.configure(
                text=f"Connected as {username}",
                text_color="#00CC00"
            )
            self.login_button.configure(text="Disconnect", command=self.logout)
            self.connect_shared_button.configure(state="normal")
            self.update_shared_servers_label()

    def logout(self):
        """Handle logout button click"""
        self.app.central_client.disconnect()

        # Update UI
        self.status_label.configure(
            text="Not connected",
            text_color="#FFFFFF"
        )
        self.login_button.configure(text="Login", command=self.login)
        self.connect_shared_button.configure(state="disabled")
        self.sharing_button.configure(state="disabled")
        self.shared_servers_label.configure(text="No shared servers available")
        self.active_conn_label.configure(text="No active connection")

    def connect_to_shared_servers(self):
        """Connect to all shared servers"""
        self.app.connect_to_shared_servers()

    def toggle_sharing(self):
        """Toggle sharing for the active connection"""
        if not self.app.active_connection:
            return

        self.app.toggle_connection_sharing(self.app.active_connection)
        self.update_sharing_button()

    def update_ui(self):
        """Update UI elements periodically"""
        # Update active connection label
        if self.app.active_connection and self.app.connection_manager.connections.get(self.app.active_connection):
            connection = self.app.connection_manager.connections[self.app.active_connection]
            host, port = connection.get('host'), connection.get('port')
            self.active_conn_label.configure(text=f"Active connection: {host}:{port}")
            self.sharing_button.configure(state="normal")
            self.update_sharing_button()
        else:
            self.active_conn_label.configure(text="No active connection")
            self.sharing_button.configure(state="disabled")

        # Update shared servers label if connected to central server
        if self.app.central_client.authenticated:
            self.update_shared_servers_label()

        # Add this code to show/hide admin panel
        if self.app.central_client.authenticated and self.app.central_client.is_admin:
            self.admin_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        else:
            self.admin_frame.pack_forget()

        # Schedule next update
        self.app.after(2000, self.update_ui)

    def update_sharing_button(self):
        """Update sharing button text based on current sharing status"""
        if not self.app.active_connection:
            return

        connection = self.app.connection_manager.connections[self.app.active_connection]
        host, port = connection.get('host'), connection.get('port')

        # Check if this connection is being shared
        is_shared = self.app.central_client.is_sharing_connection(host, port)

        if is_shared:
            self.sharing_button.configure(
                text="Disable Sharing",
                fg_color="#FF5555",
                hover_color="#FF0000"
            )
        else:
            self.sharing_button.configure(
                text="Enable Sharing",
                fg_color="#2B7DE9",
                hover_color="#1D5EAD"
            )

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