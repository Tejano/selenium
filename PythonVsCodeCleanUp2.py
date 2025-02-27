import os
import shutil
import json
import subprocess

# Get the user's home directory
home_dir = os.path.expanduser("~")

# Define VS Code paths based on OS
vscode_paths = {
    "Windows": {
        "extensions": os.path.join(home_dir, "AppData", "Roaming", "Code", "extensions"),
        "cached_extensions": os.path.join(home_dir, "AppData", "Roaming", "Code", "CachedExtensions"),
        "global_storage": os.path.join(home_dir, "AppData", "Roaming", "Code", "User", "globalStorage"),
        "user_settings": os.path.join(home_dir, "AppData", "Roaming", "Code", "User"),
        "sqlite_db": os.path.join(home_dir, "AppData", "Roaming", "Code", "User", "globalStorage", "state.vscdb"),
        "settings_json": os.path.join(home_dir, "AppData", "Roaming", "Code", "User", "settings.json"),
    },
    "Mac/Linux": {
        "extensions": os.path.join(home_dir, ".vscode", "extensions"),
        "cached_extensions": os.path.join(home_dir, ".config", "Code", "CachedExtensions"),
        "global_storage": os.path.join(home_dir, ".config", "Code", "User", "globalStorage"),
        "user_settings": os.path.join(home_dir, ".config", "Code", "User"),
        "sqlite_db": os.path.join(home_dir, ".config", "Code", "User", "globalStorage", "state.vscdb"),
        "settings_json": os.path.join(home_dir, ".config", "Code", "User", "settings.json"),
    },
}

# Detect OS
os_name = "Windows" if os.name == "nt" else "Mac/Linux"
os_paths = vscode_paths[os_name]

# Extension name to remove
extension_name = "equinusocio.vsc-material-theme"

# Function to remove a directory safely
def remove_directory(path):
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"✅ Removed: {path}")
        except Exception as e:
            print(f"❌ Error removing {path}: {e}")
    else:
        print(f"🔍 Skipped (Not Found): {path}")

# Function to remove a file safely
def remove_file(path):
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"✅ Removed: {path}")
        except Exception as e:
            print(f"❌ Error removing {path}: {e}")
    else:
        print(f"🔍 Skipped (Not Found): {path}")

# Function to update settings.json to ignore the extension in sync
def update_settings_json():
    settings_json_path = os_paths["settings_json"]
    if os.path.exists(settings_json_path):
        try:
            with open(settings_json_path, "r", encoding="utf-8") as file:
                settings_data = json.load(file)

            # Ensure "settingsSync.ignoredSettings" exists
            if "settingsSync.ignoredSettings" not in settings_data:
                settings_data["settingsSync.ignoredSettings"] = []

            # Add the extension to ignored settings if not already there
            ignored_list = settings_data["settingsSync.ignoredSettings"]
            if f"extensions.{extension_name}" not in ignored_list:
                ignored_list.append(f"extensions.{extension_name}")

            # Save back to settings.json
            with open(settings_json_path, "w", encoding="utf-8") as file:
                json.dump(settings_data, file, indent=4)

            print(f"✅ Updated {settings_json_path} to ignore syncing {extension_name}.")

        except Exception as e:
            print(f"❌ Error modifying {settings_json_path}: {e}")
    else:
        print(f"🔍 Skipped (Not Found): {settings_json_path}")

# Function to run VS Code CLI commands safely
def run_vscode_command(command):
    try:
        result = subprocess.run(["code", command, extension_name], capture_output=True, text=True)
        print(f"✅ VS Code command `{command}` executed successfully.")
        if result.stdout:
            print("Output:", result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
    except FileNotFoundError:
        print("❌ VS Code command not found. Make sure `code` is in your system PATH.")
    except Exception as e:
        print(f"❌ Error executing VS Code command `{command}`: {e}")

# Step 1: Remove extension files
print("\n🔍 Removing extension files...")
remove_directory(os.path.join(os_paths["extensions"], extension_name))
remove_directory(os_paths["cached_extensions"])
remove_directory(os.path.join(os_paths["global_storage"], extension_name))

# Step 2: Remove VS Code's SQLite database (internal extension registry)
print("\n🔍 Deleting VS Code's internal database...")
remove_file(os_paths["sqlite_db"])

# Step 3: Prevent VS Code from syncing the extension in the future
print("\n🔍 Updating settings.json to stop syncing this extension...")
update_settings_json()

# Step 4: Run VS Code CLI commands to force refresh
print("\n🔍 Running VS Code commands...")
run_vscode_command("--uninstall-extension")
run_vscode_command("--list-extensions")

# Step 5: Final cleanup messages
print("\n🚀 Cleanup complete! Restart VS Code to see the changes.")

