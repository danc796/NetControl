import socket
import json
import threading
import time
import logging
from cryptography.fernet import Fernet

class ConnectionManager:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        self.connections = {}

    def add_connection(self, host, port):
        """Add a new remote connection with auto-reconnect support"""
        # Don't try to access UI elements like self.host_entry here!

        if not host:
            self.parent_app.toast.show_toast("Please enter an IP address", "warning")
            return

        try:
            port = int(port) if port else 5000
            if port < 0 or port > 65535:
                raise ValueError("Port out of range")
        except ValueError:
            self.parent_app.toast.show_toast("Invalid port number. Please enter a number between 0-65535", "warning")
            return

        connection_id = f"{host}:{port}"

        # Check if this connection already exists
        if connection_id in self.connections:
            self.parent_app.toast.show_toast(f"Connection to {host}:{port} already exists", "warning")
            return

        # Store connection info first (even before successful connection)
        self.connections[connection_id] = {
            'socket': None,
            'cipher_suite': None,
            'host': host,
            'port': port,
            'system_info': None,
            'connection_active': False,
            'reconnect_attempts': 0,
            'last_reconnect_time': time.time()
        }

        # Add to computer list with 'Connecting' status
        self.parent_app.connection_tab.computer_list.insert('', 'end', connection_id, text=host,
                                                            values=('Connecting...',))

        # Start connection in a separate thread to avoid UI freezing
        connect_thread = threading.Thread(
            target=self.connect_to_server,
            args=(connection_id,)
        )
        connect_thread.daemon = True
        connect_thread.start()

    def connect_to_server(self, connection_id):
        """Connect to server with timeout handling and auto-reconnect support"""
        connection = self.connections.get(connection_id)
        if not connection:
            return

        host, port = connection['host'], connection['port']

        try:
            # Create socket with timeout
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(3.0)  # 3-second timeout

            # Attempt connection
            client_socket.connect((host, port))

            # Get encryption key
            key = client_socket.recv(44)  # Fernet key length
            cipher_suite = Fernet(key)

            # Update connection info
            self.connections[connection_id]['socket'] = client_socket
            self.connections[connection_id]['cipher_suite'] = cipher_suite
            self.connections[connection_id]['connection_active'] = True
            self.connections[connection_id]['reconnect_attempts'] = 0

            # Update UI from the main thread - FIX: Use parent_app.after instead of self.after
            self.parent_app.after(0, lambda: self.parent_app.connection_tab.computer_list.set(connection_id, "status",
                                                                                              "Connected"))
            self.parent_app.after(0, lambda: self.parent_app.toast.show_toast(f"Connected to {host}:{port}", "success"))

            # Start monitoring thread
            monitor_thread = threading.Thread(
                target=self.monitor_connection,
                args=(connection_id,)
            )
            monitor_thread.daemon = True
            monitor_thread.start()

        except (socket.timeout, ConnectionRefusedError) as e:
            # Handle timeouts and connection refusals
            error_msg = "Connection timed out" if isinstance(e, socket.timeout) else "Connection refused"

            # Update UI from the main thread - FIX: Use parent_app.after instead of self.after
            self.parent_app.after(0, lambda: self.parent_app.connection_tab.computer_list.set(connection_id, "status",
                                                                                              "Retrying..."))
            self.parent_app.after(0, lambda: self.parent_app.toast.show_toast(
                f"{error_msg} for {host}:{port}. Retrying...", "warning"))

            # Schedule a reconnection attempt
            self.schedule_reconnection(connection_id)

        except Exception as e:
            # Handle other errors
            self.parent_app.after(0, lambda: self.parent_app.connection_tab.computer_list.set(connection_id, "status",
                                                                                              "Error"))
            self.parent_app.after(0, lambda: self.parent_app.toast.show_toast(f"Connection error: {str(e)}", "error"))

    def remove_connection(self, connection_id):
        """Remove selected connection with proper cleanup"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]

            # Cancel any scheduled reconnection attempts
            if connection.get('scheduled_reconnect'):
                self.parent_app.after_cancel(connection['scheduled_reconnect'])

            # Close socket if it exists
            if connection.get('socket'):
                try:
                    connection['socket'].close()
                except:
                    pass

            # Remove from connections dictionary
            del self.connections[connection_id]

            # Remove from UI
            self.parent_app.connection_tab.computer_list.delete(connection_id)

            # Reset active connection if it was the one removed
            if self.parent_app.active_connection == connection_id:
                self.parent_app.active_connection = None

    def send_command(self, connection_id, command_type, data):
        """Send command with improved error handling and reconnection support"""
        connection = self.connections.get(connection_id)
        if not connection:
            print(f"No connection found for ID: {connection_id}")
            return None

        # Check if connection is active, if not try to reconnect first
        if not connection.get('connection_active', False):
            if not self.attempt_reconnection(connection_id):
                return None  # Failed to reconnect, can't send command

        try:
            # Prepare command
            command = {
                'type': command_type,
                'data': data
            }
            print(f"Sending command: {command_type}")

            # Convert to JSON
            json_data = json.dumps(command)

            # Set socket timeout based on command type
            # Use longer timeout for operations that might take longer
            if command_type in ['software_inventory', 'start_rdp', 'stop_rdp']:
                connection['socket'].settimeout(30.0)  # Longer timeout for these operations
            else:
                connection['socket'].settimeout(10.0)  # Standard timeout

            # Regular command sending
            encrypted_data = connection['cipher_suite'].encrypt(json_data.encode())
            connection['socket'].send(encrypted_data)
            print("Command sent successfully")

            # Receive response with timeout handling
            try:
                print("Waiting for response...")
                encrypted_response = connection['socket'].recv(16384)

                # Update last successful communication time
                connection['last_health_check'] = time.time()

                if not encrypted_response:
                    print("Received empty response from server")
                    # Mark connection as inactive to trigger reconnection
                    connection['connection_active'] = False
                    return None

                print(f"Received encrypted response of length: {len(encrypted_response)}")

                # Decrypt response
                try:
                    decrypted_response = connection['cipher_suite'].decrypt(encrypted_response).decode()
                    print("Response decrypted successfully")

                    # Mark as successfully communicated
                    connection['connection_active'] = True
                    connection['reconnect_attempts'] = 0

                    # Set status to Connected if it's not already
                    current_status = self.parent_app.connection_tab.computer_list.item(connection_id, "values")[0]
                    if "Connected" not in current_status:
                        self.parent_app.after(0, lambda: self.parent_app.connection_tab.computer_list.set(                            connection_id, "status", "Connected"
                        ))

                    return json.loads(decrypted_response)

                except Exception as e:
                    print(f"Decryption error: {str(e)}")
                    # Mark connection as inactive
                    connection['connection_active'] = False
                    return None

            except socket.timeout:
                print(f"Response timeout for {connection_id}")
                # Mark as potentially inactive, but don't immediately disconnect
                # Some operations like power management might not need responses
                if command_type not in ['power_management']:
                    connection['connection_active'] = False
                return None

        except ConnectionResetError:
            print(f"Connection reset for {connection_id}")
            # Mark connection as inactive to trigger reconnection
            connection['connection_active'] = False
            self.parent_app.after(0, lambda: self.parent_app.connection_tab.computer_list.set(                connection_id, "status", "Reconnecting..."
            ))
            self.schedule_reconnection(connection_id)
            return None

        except (BrokenPipeError, OSError) as e:
            print(f"Connection broken for {connection_id}: {str(e)}")
            # Mark connection as inactive to trigger reconnection
            connection['connection_active'] = False
            self.parent_app.after(0, lambda: self.parent_app.connection_tab.computer_list.set(                connection_id, "status", "Reconnecting..."
            ))
            self.schedule_reconnection(connection_id)
            return None

        except Exception as e:
            print(f"Send command error: {str(e)}")
            # Mark connection as inactive
            connection['connection_active'] = False
            return None

    def attempt_reconnection(self, connection_id):
        """Attempt to reconnect to a failed connection"""
        connection = self.connections.get(connection_id)
        if not connection:
            return False

        host, port = connection['host'], connection['port']
        print(f"Attempting to reconnect to {host}:{port}")

        try:
            # Close existing socket if any
            if connection['socket']:
                try:
                    connection['socket'].close()
                except:
                    pass

            # Create new socket with timeout
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(3.0)

            # Attempt connection
            client_socket.connect((host, port))

            # Get encryption key
            key = client_socket.recv(44)  # Fernet key length
            cipher_suite = Fernet(key)

            # Update connection info
            self.connections[connection_id]['socket'] = client_socket
            self.connections[connection_id]['cipher_suite'] = cipher_suite

            # Log the successful reconnection
            logging.info(f"Successfully reconnected to {host}:{port}")
            self.parent_app.toast.show_toast(f"Reconnected to {host}:{port}", "success")

            return True

        except (socket.timeout, ConnectionRefusedError) as e:
            error_msg = "Connection timed out" if isinstance(e, socket.timeout) else "Connection refused"
            logging.warning(f"Reconnection attempt failed: {error_msg} for {host}:{port}")
            return False

        except Exception as e:
            logging.error(f"Reconnection error: {str(e)}")
            return False

    def attempt_reconnection_from_scheduler(self, connection_id):
        """Attempt reconnection from the scheduler"""
        connection = self.connections.get(connection_id)
        if not connection:
            return

        # Clear the scheduled reconnect ID
        connection['scheduled_reconnect'] = None

        # Update UI
        self.parent_app.connection_tab.computer_list.set(connection_id, "status", "Connecting...")

        # Start a new connection thread
        connect_thread = threading.Thread(
            target=self.connect_to_server,
            args=(connection_id,)
        )
        connect_thread.daemon = True
        connect_thread.start()

    def schedule_reconnection(self, connection_id):
        """Schedule a reconnection attempt with exponential backoff"""
        connection = self.connections.get(connection_id)
        if not connection:
            return

        # Increment retry counter
        connection['reconnect_attempts'] += 1

        # Calculate backoff delay (min 2 seconds, max 60 seconds)
        # Example: 1st retry = 2s, 2nd = 4s, 3rd = 8s, etc. up to 60s max
        backoff = min(2 ** connection['reconnect_attempts'], 60)

        # Update UI
        self.parent_app.after(0, lambda: self.parent_app.connection_tab.computer_list.set(
            connection_id,
            "status",
            f"Retry in {backoff}s"
        ))

        # Schedule the reconnection
        reconnect_id = self.parent_app.after(
            backoff * 1000,  # Convert to milliseconds
            lambda: self.attempt_reconnection_from_scheduler(connection_id)
        )

        # Store the reconnection ID so we can cancel it if needed
        connection['scheduled_reconnect'] = reconnect_id
        connection['last_reconnect_time'] = time.time() + backoff

    def monitor_connection(self, connection_id):
        """Monitor individual connection with automatic reconnection"""
        connection = self.connections.get(connection_id)
        if not connection:
            return

        reconnect_delay = 5  # Initial reconnect delay in seconds
        max_reconnect_delay = 60  # Maximum reconnect delay

        while connection_id in self.connections:
            try:
                # Get system info
                response = self.send_command(connection_id, 'system_info', {})
                if response and response.get('status') == 'success':
                    self.connections[connection_id]['system_info'] = response['data']
                    # Reset reconnect delay on successful communication
                    reconnect_delay = 5
                    # Update status in computer list
                    self.parent_app.connection_tab.computer_list.set(connection_id, "status", "Connected")
                    self.connections[connection_id]['connection_active'] = True
                else:
                    # Handle failed response
                    raise ConnectionError("Invalid response from server")

            except Exception as e:
                print(f"Monitoring error for {connection_id}: {str(e)}")
                self.parent_app.connection_tab.computer_list.set(connection_id, "status", "Reconnecting...")
                self.connections[connection_id]['connection_active'] = False

                # Attempt to reconnect
                if self.attempt_reconnection(connection_id):
                    # Successfully reconnected, reset delay
                    reconnect_delay = 5
                    self.parent_app.connection_tab.computer_list.set(connection_id, "status", "Connected")
                    self.connections[connection_id]['connection_active'] = True
                else:
                    # Failed to reconnect, back off and try again later
                    self.parent_app.connection_tab.computer_list.set(connection_id, "status",
                                                                     f"Retry in {reconnect_delay}s")
                    time.sleep(reconnect_delay)
                    # Exponential backoff with maximum
                    reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)

            time.sleep(5)  # Check every 5 seconds

    def initialize_connection_monitoring(self):
        """Initialize connection monitoring thread"""
        # Start connection health monitoring thread
        self.connection_monitor_thread = threading.Thread(
            target=self.monitor_connection_health,
            daemon=True
        )
        self.connection_monitor_thread.start()
        logging.info("Connection health monitoring thread started")

    def monitor_connection_health(self):
        """Periodically check all connections and initiate reconnects as needed"""
        logging.info("Starting connection health monitoring")

        while getattr(self.parent_app, 'running', True):
            try:
                # Iterate through a copy of the connections dict to avoid modification during iteration
                for conn_id, connection in list(self.connections.items()):
                    # Skip connections that are already in reconnection process
                    if connection.get('scheduled_reconnect'):
                        continue

                    # Skip active connections that were recently checked
                    if connection.get('connection_active') and connection.get('last_health_check'):
                        # Only check active connections every 30 seconds
                        if time.time() - connection.get('last_health_check', 0) < 30:
                            continue

                    # Check connection status
                    try:
                        # Very simple ping without extensive processing
                        if connection.get('socket') and connection.get('cipher_suite'):
                            # Send a small ping command
                            try:
                                connection['socket'].settimeout(2.0)  # Short timeout for health check
                                ping_cmd = json.dumps({'type': 'ping', 'data': {}})
                                encrypted_data = connection['cipher_suite'].encrypt(ping_cmd.encode())
                                connection['socket'].send(encrypted_data)

                                # Wait for response
                                encrypted_response = connection['socket'].recv(1024)
                                if encrypted_response:
                                    # If we got any response, mark as active
                                    connection['connection_active'] = True
                                    connection['last_health_check'] = time.time()
                                    connection['reconnect_attempts'] = 0  # Reset counter on success
                                    # Update UI if status doesn't show "Connected"
                                    current_status = self.parent_app.connection_tab.computer_list.item(conn_id, "values")[0]
                                    if "Connected" not in current_status:
                                        self.parent_app.after(0, lambda id=conn_id: self.parent_app.connection_tab.computer_list.set(
                                            id, "status", "Connected"
                                        ))
                                else:
                                    # Empty response, connection may be broken
                                    raise ConnectionError("Empty response")

                            except (socket.timeout, ConnectionError, BrokenPipeError, OSError) as e:
                                # Connection appears to be down
                                connection['connection_active'] = False
                                current_status = self.parent_app.connection_tab.computer_list.item(conn_id, "values")[0]
                                if "Reconnecting" not in current_status:
                                    self.parent_app.after(0, lambda id=conn_id: self.parent_app.connection_tab.computer_list.set(
                                        id, "status", "Reconnecting..."
                                    ))
                                self.schedule_reconnection(conn_id)

                    except Exception as e:
                        logging.error(f"Health check error for {conn_id}: {str(e)}")

                # Sleep between checks
                time.sleep(5)

            except Exception as e:
                logging.error(f"Connection health monitoring error: {str(e)}")
                time.sleep(10)  # Longer sleep on error

    def close_all_connections(self):
        """Close all active connections"""
        try:
            for conn_id in list(self.connections.keys()):
                try:
                    connection = self.connections.get(conn_id)
                    if connection:
                        # Cancel any scheduled reconnection attempts
                        if connection.get('scheduled_reconnect'):
                            self.parent_app.after_cancel(connection['scheduled_reconnect'])

                        # Close socket if it exists
                        if connection.get('socket'):
                            try:
                                connection['socket'].close()
                            except:
                                pass

                except Exception as e:
                    logging.error(f"Error closing connection {conn_id}: {str(e)}")

            # Clear all connections
            self.connections.clear()
            logging.info("All connections closed")

        except Exception as e:
            logging.error(f"Error in close_all_connections: {str(e)}")