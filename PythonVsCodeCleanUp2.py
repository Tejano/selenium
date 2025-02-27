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
    },
    "Mac/Linux": {
        "extensions": os.path.join(home_dir, ".vscode", "extensions"),
        "cached_extensions": os.path.join(home_dir, ".config", "Code", "CachedExtensions"),
        "global_storage": os.path.join(home_dir, ".config", "Code", "User", "globalStorage"),
        "user_settings": os.path.join(home_dir, ".config", "Code", "User"),
        "sqlite_db": os.path.join(home_dir, ".config", "Code", "User", "globalStorage", "state.vscdb"),
    },
}

# Detect OS
if os.name == "nt":
    os_paths = vscode_paths["Windows"]
else:
    os_paths = vscode_paths["Mac/Linux"]

# Extension name to remove
extension_name = "equinusocio.vsc.material-theme"

# Function to remove a directory if it exists
def remove_directory(path):
    if os.path.exists(path):
        try:
            shutil.rmtree(path)
            print(f"✅ Removed: {path}")
        except Exception as e:
            print(f"❌ Error removing {path}: {e}")

# Function to remove a file if it exists
def remove_file(path):
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"✅ Removed: {path}")
        except Exception as e:
            print(f"❌ Error removing {path}: {e}")

# Function to update extensions.json
def update_extensions_json():
    extensions_json_path = os.path.join(os_paths["user_settings"], "extensions.json")
    if os.path.exists(extensions_json_path):
        try:
            with open(extensions_json_path, "r", encoding="utf-8") as file:
                extensions_data = json.load(file)

            if isinstance(extensions_data, list):
                extensions_data = [ext for ext in extensions_data if extension_name not in str(ext)]
            elif isinstance(extensions_data, dict) and "disabled" in extensions_data:
                extensions_data["disabled"] = [
                    ext for ext in extensions_data["disabled"] if extension_name not in ext
                ]

            with open(extensions_json_path, "w", encoding="utf-8") as file:
                json.dump(extensions_data, file, indent=4)

            print(f"✅ Updated {extensions_json_path} to remove extension entry.")

        except Exception as e:
            print(f"❌ Error modifying {extensions_json_path}: {e}")

# Function to run VS Code CLI commands
def run_vscode_command(command):
    try:
        result = subprocess.run(["code", command, extension_name], capture_output=True, text=True)
        print(f"✅ VS Code command `{command}` executed successfully.")
        if result.stdout:
            print("Output:", result.stdout)
        if result.stderr:
            print("Error:", result.stderr)
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

# Step 3: Remove the extension from `extensions.json`
print("\n🔍 Cleaning up extensions.json...")
update_extensions_json()

# Step 4: Run VS Code CLI commands to force refresh
print("\n🔍 Running VS Code commands...")
run_vscode_command("--uninstall-extension")
run_vscode_command("--list-extensions")

# Step 5: Final cleanup messages
print("\n🚀 Cleanup complete! Restart VS Code to see the changes.")
