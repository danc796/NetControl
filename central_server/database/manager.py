"""
Database manager for the Central Management Server.
Handles database operations for users, servers, and connections.
"""

import sqlite3
import logging
import hashlib
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path="central_server.db"):
        self.db_path = db_path

    def get_connection(self):
        """Get a database connection"""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # This enables column access by name
            return conn
        except Exception as e:
            logging.error(f"Database connection error: {e}")
            return None

    # User Management
    def authenticate_user(self, username, password):
        """Authenticate a user by username and password"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Hash the password for comparison
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            cursor.execute(
                "SELECT * FROM users WHERE username = ? AND password_hash = ?",
                (username, password_hash)
            )

            user = cursor.fetchone()

            if user:
                # Update last login timestamp
                cursor.execute(
                    "UPDATE users SET last_login = ? WHERE user_id = ?",
                    (datetime.now(), user['user_id'])
                )
                conn.commit()

            conn.close()
            return dict(user) if user else None

        except Exception as e:
            logging.error(f"Authentication error: {e}")
            return None

    def create_user(self, username, password, is_admin=0):
        """Create a new user"""
        try:
            # Check if username already exists
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return False, "Username already exists"

            # Hash the password and create the user
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                (username, password_hash, is_admin)
            )

            conn.commit()
            conn.close()
            return True, "User created successfully"

        except Exception as e:
            logging.error(f"Error creating user: {e}")
            return False, str(e)

    def get_all_users(self):
        """Get all users"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT user_id, username, created_at, last_login, is_admin FROM users")
            users = [dict(row) for row in cursor.fetchall()]

            conn.close()
            return users
        except Exception as e:
            logging.error(f"Error getting users: {e}")
            return []

    # Server Management
    def register_server(self, ip_address, port, user_id):
        """Register a server that a user is connected to"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # First, ensure the server exists in the servers table
            cursor.execute(
                """
                INSERT OR IGNORE INTO servers (ip_address, port) 
                VALUES (?, ?)
                """,
                (ip_address, port)
            )

            # Get the server_id
            cursor.execute(
                "SELECT server_id FROM servers WHERE ip_address = ? AND port = ?",
                (ip_address, port)
            )
            server_record = cursor.fetchone()

            if not server_record:
                conn.close()
                return False, "Failed to register server"

            server_id = server_record['server_id']

            # Update the last_seen timestamp
            cursor.execute(
                "UPDATE servers SET last_seen = ? WHERE server_id = ?",
                (datetime.now(), server_id)
            )

            # Add to active connections if not already there
            cursor.execute(
                """
                INSERT OR IGNORE INTO active_connections 
                (user_id, server_id, connected_at, is_shared) 
                VALUES (?, ?, ?, 0)
                """,
                (user_id, server_id, datetime.now())
            )

            # If connection already existed, update the connected_at time
            if cursor.rowcount == 0:
                cursor.execute(
                    """
                    UPDATE active_connections
                    SET connected_at = ?
                    WHERE user_id = ? AND server_id = ?
                    """,
                    (datetime.now(), user_id, server_id)
                )

            conn.commit()
            conn.close()
            return True, "Server registered successfully"

        except Exception as e:
            logging.error(f"Error registering server: {e}")
            return False, str(e)

    def unregister_server(self, ip_address, port, user_id):
        """Unregister a server that a user has disconnected from"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Get the server_id
            cursor.execute(
                "SELECT server_id FROM servers WHERE ip_address = ? AND port = ?",
                (ip_address, port)
            )
            server_record = cursor.fetchone()

            if not server_record:
                conn.close()
                return False, "Server not found"

            server_id = server_record['server_id']

            # Get the connection record
            cursor.execute(
                "SELECT connection_id, connected_at FROM active_connections WHERE user_id = ? AND server_id = ?",
                (user_id, server_id)
            )
            connection = cursor.fetchone()

            if connection:
                # Remove from active connections
                cursor.execute(
                    "DELETE FROM active_connections WHERE connection_id = ?",
                    (connection['connection_id'],)
                )

            conn.commit()
            conn.close()
            return True, "Server unregistered successfully"

        except Exception as e:
            logging.error(f"Error unregistering server: {e}")
            return False, str(e)

    def set_connection_sharing(self, user_id, ip_address, port, is_shared):
        """Set whether a connection is shared or not"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Get the server_id
            cursor.execute(
                "SELECT server_id FROM servers WHERE ip_address = ? AND port = ?",
                (ip_address, port)
            )
            server_record = cursor.fetchone()

            if not server_record:
                conn.close()
                return False, "Server not found"

            server_id = server_record['server_id']

            # Update the sharing status
            cursor.execute(
                """
                UPDATE active_connections
                SET is_shared = ?
                WHERE user_id = ? AND server_id = ?
                """,
                (1 if is_shared else 0, user_id, server_id)
            )

            conn.commit()
            conn.close()

            return True, "Connection sharing status updated"

        except Exception as e:
            logging.error(f"Error setting connection sharing: {e}")
            return False, str(e)

    def get_all_active_servers(self):
        """Get all servers that are actively connected to by any user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT s.ip_address, s.port, COUNT(ac.connection_id) as users_connected
                FROM servers s
                JOIN active_connections ac ON s.server_id = ac.server_id
                GROUP BY s.server_id
                """
            )

            servers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return servers

        except Exception as e:
            logging.error(f"Error getting active servers: {e}")
            return []

    def get_shared_servers(self):
        """Get all servers that are marked as shared by any user"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT s.ip_address, s.port
                FROM servers s
                JOIN active_connections ac ON s.server_id = ac.server_id
                WHERE ac.is_shared = 1
                """
            )

            servers = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return servers

        except Exception as e:
            logging.error(f"Error getting shared servers: {e}")
            return []

    def get_user_connections(self, user_id):
        """Get all servers a user is connected to"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT s.ip_address, s.port, ac.is_shared
                FROM servers s
                JOIN active_connections ac ON s.server_id = ac.server_id
                WHERE ac.user_id = ?
                """,
                (user_id,)
            )

            connections = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return connections

        except Exception as e:
            logging.error(f"Error getting user connections: {e}")
            return []