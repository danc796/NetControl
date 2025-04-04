import socket
import threading
import json
import logging
import time
from cryptography.fernet import Fernet
from datetime import datetime

from nc_server.connection.encryption import create_encryption_key
from nc_server.monitoring.system_info import get_system_info
from nc_server.monitoring.hardware import get_hardware_info
from nc_server.monitoring.network import get_network_info
from nc_server.software.inventory import get_software_inventory
from nc_server.power.controller import handle_power_action
from nc_server.rdp.server import RDPServer


class ConnectionManager:
    def __init__(self, host='0.0.0.0', port=5000):
        """Initialize the connection manager"""
        logging.info("Initializing nc Server Connection Manager")

        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients = {}
        self.encryption_key = create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        self.running = True

        self.rdp_server = None
        self.rdp_thread = None

        # Command handlers mapping
        self.command_handlers = {
            'system_info': self.handle_system_info,
            'hardware_monitor': self.handle_hardware_monitor,
            'software_inventory': self.handle_software_inventory,
            'power_management': self.handle_power_management,
            'execute_command': self.handle_command_execution,
            'network_monitor': self.handle_network_monitor,
            'start_rdp': self.handle_start_rdp,
            'stop_rdp': self.handle_stop_rdp,
            'ping': self.handle_ping
        }

    def start(self):
        """Start the server and listen for connections"""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)

            logging.info(f"Server started on {self.host}:{self.port}")

            while self.running:
                try:
                    client_socket, address = self.server_socket.accept()
                    logging.info(f"New connection from {address}")

                    # Start client handler thread
                    client_handler = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_handler.daemon = True
                    client_handler.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logging.error(f"Error accepting connection: {e}")
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            self.stop()

    def handle_client(self, client_socket, address):
        """Handle client connection"""
        try:
            client_socket.settimeout(1.0)

            # Send encryption key
            client_socket.send(self.encryption_key)

            # Store client information
            self.clients[address] = {
                'socket': client_socket,
                'last_seen': datetime.now(),
                'system_info': get_system_info()
            }

            # Main communication loop
            while self.running:
                try:
                    # Receive encrypted data
                    encrypted_data = client_socket.recv(4096)
                    if not encrypted_data:
                        break

                    # Decrypt and process command
                    data = self.cipher_suite.decrypt(encrypted_data).decode()
                    command = json.loads(data)
                    response = self.process_command(command)

                    # Encrypt and send response
                    encrypted_response = self.cipher_suite.encrypt(json.dumps(response).encode())
                    client_socket.send(encrypted_response)

                except socket.timeout:
                    continue
                except Exception as e:
                    logging.error(f"Error handling client {address}: {e}")
                    break

        except Exception as e:
            logging.error(f"Client handler error for {address}: {e}")
        finally:
            # Clean up client connection
            self.clients.pop(address, None)
            try:
                client_socket.close()
            except:
                pass
            logging.info(f"Connection closed from {address}")

    def process_command(self, command):
        """Process client command and return response"""
        try:
            cmd_type = command.get('type', '')
            cmd_data = command.get('data', {})

            # Debug logging
            logging.debug(f"Received command: {cmd_type} with data: {cmd_data}")

            # Get the appropriate handler for this command type
            handler = self.command_handlers.get(cmd_type)

            if handler:
                # Ensure cmd_data is a dictionary
                if not isinstance(cmd_data, dict):
                    cmd_data = {}

                # Call the handler with the command data
                return handler(cmd_data)
            else:
                logging.warning(f"Unknown command received: {cmd_type}")
                return {'status': 'error', 'message': f'Unknown command: {cmd_type}'}

        except Exception as e:
            logging.error(f"Error processing command: {str(e)}")
            return {'status': 'error', 'message': 'Internal server error'}

    def handle_system_info(self, data):
        """Handle system information request"""
        return {
            'status': 'success',
            'data': get_system_info()
        }

    def handle_hardware_monitor(self, data):
        """Handle hardware monitoring request"""
        return {
            'status': 'success',
            'data': get_hardware_info()
        }

    def handle_software_inventory(self, data):
        """Handle software inventory request"""
        search_term = data.get('search', '')
        return get_software_inventory(search_term)

    def handle_power_management(self, data):
        """Handle power management request"""
        action = data.get('action')
        seconds = data.get('seconds')
        return handle_power_action(action, seconds)

    def handle_command_execution(self, data):
        """Handle command execution request"""
        import subprocess
        command = data.get('command')
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                'status': 'success',
                'data': {
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'return_code': result.returncode
                }
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def handle_network_monitor(self, data):
        """Handle network monitoring request"""
        return {
            'status': 'success',
            'data': get_network_info()
        }

    def handle_ping(self, data):
        """Handle ping request (for connection testing)"""
        return {
            'status': 'success',
            'message': 'pong'
        }

    def handle_start_rdp(self, data):
        """Start RDP server"""
        try:
            # Force close any existing RDP server
            if self.rdp_server is not None:
                logging.info("Stopping existing RDP server before starting a new one")
                self.rdp_server.stop()
                self.rdp_server = None

                # Wait for thread to terminate
                if self.rdp_thread and self.rdp_thread.is_alive():
                    self.rdp_thread.join(timeout=2)
                    self.rdp_thread = None

                # Wait for resources to be released
                time.sleep(1)

            # Use the actual server's IP
            rdp_host = socket.gethostbyname(socket.gethostname())
            rdp_port = 5900  # Default RDP port

            # Create and start RDP server
            self.rdp_server = RDPServer(host='0.0.0.0', port=rdp_port)
            self.rdp_thread = threading.Thread(target=self.rdp_server.start)
            self.rdp_thread.daemon = True
            self.rdp_thread.start()

            # Wait for server to start
            time.sleep(1.5)

            return {
                'status': 'success',
                'data': {
                    'ip': rdp_host,
                    'port': rdp_port
                }
            }
        except Exception as e:
            logging.error(f"Failed to start RDP server: {e}")

            # Clean up in case of error
            if hasattr(self, 'rdp_server') and self.rdp_server:
                try:
                    self.rdp_server.stop()
                    self.rdp_server = None
                except:
                    pass

            return {
                'status': 'error',
                'message': str(e)
            }

    def handle_stop_rdp(self, data):
        """Stop RDP server"""
        try:
            if self.rdp_server:
                logging.info("Stopping RDP server")
                self.rdp_server.stop()
                self.rdp_server = None

                # Clean up thread reference
                if self.rdp_thread:
                    if self.rdp_thread.is_alive():
                        self.rdp_thread.join(timeout=3)
                    self.rdp_thread = None

                return {'status': 'success', 'message': 'RDP server stopped successfully'}
            else:
                return {'status': 'success', 'message': 'No RDP server was running'}
        except Exception as e:
            logging.error(f"Error stopping RDP server: {e}")

            # Force reset server state even if there's an error
            self.rdp_server = None
            self.rdp_thread = None

            return {'status': 'error', 'message': f'Error stopping RDP server: {e}'}

    def stop(self):
        """Stop the server and clean up connections"""
        logging.info("Shutting down server...")
        self.running = False

        # Close all client connections
        for client in list(self.clients.values()):
            try:
                client['socket'].close()
            except:
                pass

        # Close server socket
        try:
            self.server_socket.close()
        except:
            pass

        # Stop RDP server if running
        if self.rdp_server:
            try:
                self.rdp_server.stop()
            except:
                pass

        logging.info("Server shutdown complete")