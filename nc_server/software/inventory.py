import platform
import winreg

def get_software_inventory(search_term=""):
    """Get installed software inventory with improved registry handling"""
    print("\n=== Starting Software Inventory Scan ===")
    software_list = []

    try:
        if platform.system() != 'Windows':
            return {
                'status': 'error',
                'message': 'Not a Windows system'
            }

        # Registry paths to check
        keys_to_check = [
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall'),
            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall'),
            (winreg.HKEY_CURRENT_USER, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall')
        ]

        seen_programs = set()

        for reg_root, key_path in keys_to_check:
            reg_key = None
            try:
                reg_key = winreg.OpenKey(reg_root, key_path)
                subkey_count, _, _ = winreg.QueryInfoKey(reg_key)

                for i in range(subkey_count):
                    subkey = None
                    try:
                        subkey_name = winreg.EnumKey(reg_key, i)
                        subkey = winreg.OpenKey(reg_key, subkey_name)

                        try:
                            name = winreg.QueryValueEx(subkey, "DisplayName")[0].strip()
                            if not name or name in seen_programs:
                                continue

                            # Apply search filter if provided
                            if search_term and search_term.lower() not in name.lower():
                                continue

                            version = "N/A"
                            try:
                                version = winreg.QueryValueEx(subkey, "DisplayVersion")[0].strip()
                            except (WindowsError, KeyError):
                                pass

                            # Skip system components and irrelevant entries
                            skip_keywords = [
                                "update", "microsoft", "windows", "cache", "installer",
                                "pack", "driver", "system", "component", "setup",
                                "prerequisite", "runtime", "application", "sdk"
                            ]

                            if any(keyword in name.lower() for keyword in skip_keywords):
                                continue

                            software_list.append({
                                'name': name,
                                'version': version
                            })
                            seen_programs.add(name)

                        except (WindowsError, KeyError):
                            continue

                    except WindowsError:
                        continue
                    finally:
                        if subkey is not None:
                            winreg.CloseKey(subkey)

            except WindowsError as e:
                print(f"Error accessing {key_path}: {e}")
            finally:
                if reg_key is not None:
                    winreg.CloseKey(reg_key)

        # Sort the list by program name
        software_list.sort(key=lambda x: x['name'].lower())

        print(f"\nTotal programs found: {len(software_list)}")
        return {
            'status': 'success',
            'data': software_list
        }

    except Exception as e:
        error_msg = f"Error in software inventory: {e}"
        print(f"ERROR: {error_msg}")
        return {
            'status': 'error',
            'message': error_msg
        }