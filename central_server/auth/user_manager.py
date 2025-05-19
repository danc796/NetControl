"""
User Manager for the Central Management Server.
Handles user authentication, creation, and management.
"""

import logging
import hashlib
from datetime import datetime


class UserManager:
    def __init__(self, database_manager):
        """Initialize the user manager with a database manager"""
        self.db = database_manager

    def authenticate_user(self, username, password):
        """Authenticate a user with username and password"""
        user = self.db.authenticate_user(username, password)
        if user:
            return True, user
        return False, None

    def create_user(self, username, password, is_admin=False):
        """Create a new user"""
        if not username or not password:
            return False, "Username and password are required"

        # Password validation
        if len(password) < 6:
            return False, "Password must be at least 6 characters long"

        # Create the user
        success, message = self.db.create_user(username, password, 1 if is_admin else 0)
        return success, message

    def get_all_users(self):
        """Get list of all users"""
        return self.db.get_all_users()

    def change_password(self, user_id, old_password, new_password):
        """Change a user's password"""
        # This would require additional database functionality
        # For now, we'll return a placeholder
        return False, "Not implemented"

    def delete_user(self, user_id):
        """Delete a user"""
        # This would require additional database functionality
        # For now, we'll return a placeholder
        return False, "Not implemented"

    def promote_to_admin(self, user_id):
        """Promote a user to admin status"""
        # This would require additional database functionality
        # For now, we'll return a placeholder
        return False, "Not implemented"

    def create_user_as_admin(self, admin_user_id, new_username, new_password, is_new_admin=False):
        """Create a new user when requested by an admin"""
        # Verify the requesting user is an admin
        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT is_admin FROM users WHERE user_id = ?", (admin_user_id,))
            user = cursor.fetchone()

            if not user or not user['is_admin']:
                conn.close()
                return False, "Unauthorized: Admin privileges required"

            # Now create the new user
            if not new_username or not new_password:
                return False, "Username and password are required"

            # Password validation
            if len(new_password) < 6:
                return False, "Password must be at least 6 characters long"

            # Check if username already exists
            cursor.execute("SELECT username FROM users WHERE username = ?", (new_username,))
            if cursor.fetchone():
                conn.close()
                return False, "Username already exists"

            # Create the user
            password_hash = hashlib.sha256(new_password.encode()).hexdigest()

            cursor.execute(
                "INSERT INTO users (username, password_hash, is_admin) VALUES (?, ?, ?)",
                (new_username, password_hash, 1 if is_new_admin else 0)
            )

            conn.commit()
            conn.close()

            return True, f"User '{new_username}' created successfully"

        except Exception as e:
            logging.error(f"Error creating user as admin: {e}")
            return False, str(e)