from tkinter import messagebox
import logging
from datetime import datetime


class PowerManager:
    def __init__(self, parent_app):
        self.parent_app = parent_app
        # Keep a reference to the connection manager for sending commands
        self.connection_manager = parent_app.connection_manager
        # Reference to the power status label (will be set by PowerTab)
        self.power_status = None


    def set_power_status(self, status_label):
        """Set reference to power status label from PowerTab"""
        self.power_status = status_label

    def update_power_status(self, message, color="white"):
        """Update power status label with proper error handling"""
        try:
            if hasattr(self, 'power_status') and self.power_status and self.power_status.winfo_exists():
                self.power_status.configure(text=message, text_color=color)
        except Exception as e:
            logging.error(f"Error updating power status: {str(e)}")

    def power_action_with_confirmation(self, action, confirm_msg, power_mode):
        """Execute power action with confirmation for single or multiple computers"""
        try:
            if power_mode == "all":
                self._handle_all_computers_action(action, confirm_msg)
            else:
                self._handle_single_computer_action(action, confirm_msg)
        except Exception as e:
            self.update_power_status(f"Error: {str(e)}", "red")
            logging.error(f"Power action error: {str(e)}")

    def _handle_all_computers_action(self, action, confirm_msg):
        """Handle power action for all computers"""
        if not self.connection_manager.connections:
            self.update_power_status("No computers connected", "red")
            return

        if messagebox.askyesno("Confirm Action", f"{confirm_msg} (All Computers)"):
            failed_computers = []
            successful_computers = []

            for conn_id in list(self.connection_manager.connections.keys()):  # Create a copy of keys
                connection = self.connection_manager.connections.get(conn_id)
                if not connection:
                    continue

                host = connection.get('host', 'Unknown')
                success = self._execute_power_action_for_connection(conn_id, connection, action, host)

                if success:
                    successful_computers.append(host)
                else:
                    failed_computers.append(host)

            # Update status based on results
            self._update_status_for_multiple_computers(action, successful_computers, failed_computers)

    def _handle_single_computer_action(self, action, confirm_msg):
        """Handle power action for single computer"""
        if not self.parent_app.active_connection:
            self.update_power_status("Please select a computer first", "red")
            return

        connection = self.connection_manager.connections.get(self.parent_app.active_connection)
        if not connection:
            self.update_power_status("Connection not found", "red")
            return

        host = connection.get('host', 'Unknown')

        if messagebox.askyesno("Confirm Action", confirm_msg):
            success = self._execute_power_action_for_connection(
                self.parent_app.active_connection,
                connection,
                action,
                host
            )

            if success:
                self.update_power_status(f"{action.capitalize()} command sent successfully", "green")
            else:
                self.update_power_status(f"Failed to execute {action}", "red")

    def _execute_power_action_for_connection(self, conn_id, connection, action, host):
        """Execute power action for a specific connection"""
        try:
            # Update status to show action in progress
            self.parent_app.connection_tab.computer_list.set(conn_id, "status", f"Sending {action}...")

            # Send command with timeout handling
            response = self.connection_manager.send_command(conn_id, 'power_management', {
                'action': action
            })

            if response and response.get('status') == 'success':
                self.parent_app.connection_tab.computer_list.set(conn_id, "status", "Connected")
                return True
            else:
                # Mark connection as inactive to trigger reconnection
                connection['connection_active'] = False
                self.parent_app.connection_tab.computer_list.set(conn_id, "status", "Reconnecting...")
                # Schedule immediate reconnection
                self.connection_manager.schedule_reconnection(conn_id)
                return False

        except Exception as e:
            # Mark connection as inactive to trigger reconnection
            connection['connection_active'] = False
            self.parent_app.connection_tab.computer_list.set(conn_id, "status", "Reconnecting...")
            # Schedule immediate reconnection
            self.connection_manager.schedule_reconnection(conn_id)

            # Log the error
            logging.error(f"Power action error for {host}: {str(e)}")
            return False

    def _update_status_for_multiple_computers(self, action, successful_computers, failed_computers):
        """Update status after executing action on multiple computers"""
        if not failed_computers and successful_computers:
            self.update_power_status(f"{action.capitalize()} initiated for all computers", "green")
            self.parent_app.toast.show_toast(f"{action.capitalize()} successfully sent to all computers", "success")
        elif failed_computers and successful_computers:
            self.update_power_status(
                f"{action.capitalize()} succeeded for {len(successful_computers)} computers, "
                f"failed for {len(failed_computers)} computers",
                "orange"
            )
            self.parent_app.toast.show_toast(
                f"Failed for: {', '.join(failed_computers[:3])}"
                f"{' and others' if len(failed_computers) > 3 else ''}. Reconnecting...",
                "warning"
            )
        else:
            self.update_power_status(f"{action.capitalize()} failed for all computers", "red")
            self.parent_app.toast.show_toast("Attempting to reconnect to all computers...", "error")

    def schedule_shutdown(self, time_str, power_mode):
        """Schedule a shutdown for the selected computer(s)"""
        try:
            if not time_str:
                self.update_power_status("Please enter time in HH:MM format", "red")
                return

            # Parse and validate time
            seconds_until_shutdown = self._calculate_seconds_until_time(time_str)
            if seconds_until_shutdown is None:
                return

            if power_mode == "all":
                self._schedule_shutdown_all(time_str, seconds_until_shutdown)
            else:
                self._schedule_shutdown_single(time_str, seconds_until_shutdown)

        except Exception as e:
            self.update_power_status(f"Error: {str(e)}", "red")
            logging.error(f"Schedule shutdown error: {str(e)}")

    def _calculate_seconds_until_time(self, time_str):
        """Calculate seconds until the specified time"""
        try:
            # Parse the time
            hours, minutes = map(int, time_str.split(':'))
            if not (0 <= hours <= 23 and 0 <= minutes <= 59):
                raise ValueError("Invalid time values")

            # Calculate seconds until shutdown
            current_time = datetime.now()
            target_time = current_time.replace(hour=hours, minute=minutes, second=0, microsecond=0)

            # If the time has already passed today, schedule for tomorrow
            if target_time <= current_time:
                target_time = target_time.replace(day=current_time.day + 1)

            seconds_until_shutdown = int((target_time - current_time).total_seconds())
            return seconds_until_shutdown

        except ValueError:
            self.update_power_status("Invalid time format. Use HH:MM", "red")
            return None

    def _schedule_shutdown_all(self, time_str, seconds_until_shutdown):
        """Schedule shutdown for all computers"""
        if messagebox.askyesno("Confirm Action", "Schedule shutdown for all computers?"):
            failed_computers = []
            successful_computers = []

            for conn_id in list(self.connection_manager.connections.keys()):
                connection = self.connection_manager.connections.get(conn_id)
                if not connection:
                    continue

                host = connection.get('host', 'Unknown')
                success = self._execute_scheduled_shutdown_for_connection(
                    conn_id, connection, seconds_until_shutdown, host
                )

                if success:
                    successful_computers.append(host)
                else:
                    failed_computers.append(host)

            # Update status based on results
            self._update_scheduled_shutdown_status(time_str, successful_computers, failed_computers)

    def _schedule_shutdown_single(self, time_str, seconds_until_shutdown):
        """Schedule shutdown for single computer"""
        if not self.parent_app.active_connection:
            self.update_power_status("Please select a computer first", "red")
            return

        connection = self.connection_manager.connections.get(self.parent_app.active_connection)
        if not connection:
            self.update_power_status("Connection not found", "red")
            return

        host = connection.get('host', 'Unknown')
        success = self._execute_scheduled_shutdown_for_connection(
            self.parent_app.active_connection,
            connection,
            seconds_until_shutdown,
            host
        )

        if success:
            self.update_power_status(
                f"Shutdown scheduled successfully for {time_str}",
                "green"
            )
        else:
            self.update_power_status("Failed to schedule shutdown", "red")

    def _execute_scheduled_shutdown_for_connection(self, conn_id, connection, seconds, host):
        """Execute scheduled shutdown for a specific connection"""
        try:
            # Update status to show action in progress
            self.parent_app.connection_tab.computer_list.set(conn_id, "status", "Scheduling...")

            response = self.connection_manager.send_command(conn_id, 'power_management', {
                'action': 'shutdown',
                'seconds': seconds
            })

            if response and response.get('status') == 'success':
                self.parent_app.connection_tab.computer_list.set(conn_id, "status", "Connected")
                return True
            else:
                # Mark for reconnection
                connection['connection_active'] = False
                self.parent_app.connection_tab.computer_list.set(conn_id, "status", "Reconnecting...")
                # Schedule immediate reconnection
                self.connection_manager.schedule_reconnection(conn_id)
                return False

        except Exception as e:
            # Mark for reconnection
            connection['connection_active'] = False
            self.parent_app.connection_tab.computer_list.set(conn_id, "status", "Reconnecting...")
            # Schedule immediate reconnection
            self.connection_manager.schedule_reconnection(conn_id)

            # Log the error
            logging.error(f"Schedule shutdown error for {host}: {str(e)}")
            return False

    def _update_scheduled_shutdown_status(self, time_str, successful_computers, failed_computers):
        """Update status after scheduling shutdown for multiple computers"""
        if not failed_computers and successful_computers:
            self.update_power_status("Shutdown scheduled for all computers", "green")
            self.parent_app.toast.show_toast(f"Shutdown scheduled for all computers at {time_str}", "success")
        elif failed_computers and successful_computers:
            self.update_power_status(
                f"Scheduling succeeded for {len(successful_computers)} computers, "
                f"failed for {len(failed_computers)} computers",
                "orange"
            )
            self.parent_app.toast.show_toast(
                f"Failed for: {', '.join(failed_computers[:3])}"
                f"{' and others' if len(failed_computers) > 3 else ''}. Reconnecting...",
                "warning"
            )
        else:
            self.update_power_status("Scheduling failed for all computers", "red")
            self.parent_app.toast.show_toast("Attempting to reconnect to all computers...", "error")