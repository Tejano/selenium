import os
import shutil
import json
import subprocess

# Get the user's home directory
home_dir = os.path.expanduser("~")

# Define VS Code paths
vscode_paths = {
    "Windows": {
        "extensions": os.path.join(home_dir, "AppData", "Roaming", "Code", "extensions"),
        "cached_extensions": os.path.join(home_dir, "AppData", "Roaming", "Code", "CachedExtensions"),
        "global_storage": os.path.join(home_dir, "AppData", "Roaming", "Code", "User", "globalStorage"),
        "user_settings": os.path.join(home_dir, "AppData", "Roaming", "Code", "User"),
    },
    "Mac/Linux": {
        "extensions": os.path.join(home_dir, ".vscode", "extensions"),
        "cached_extensions": os.path.join(home_dir, ".config", "Code", "CachedExtensions"),
        "global_storage": os.path.join(home_dir, ".config", "Code", "User", "globalStorage"),
        "user_settings": os.path.join(home_dir, ".config", "Code", "User"),
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

# Function to remove extension from extensions.json
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

# Function to run VS Code commands
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

# Remove extension folders
remove_directory(os.path.join(os_paths["extensions"], extension_name))

# Remove cached extension data
remove_directory(os_paths["cached_extensions"])

# Remove global storage data
remove_directory(os.path.join(os_paths["global_storage"], extension_name))

# Remove from extensions.json
update_extensions_json()

# Remove user settings that might reference the extension
remove_file(os.path.join(os_paths["user_settings"], "workbench.storage.json"))
remove_file(os.path.join(os_paths["user_settings"], "machineSettings.json"))

# Run VS Code CLI commands to force remove the extension
run_vscode_command("--uninstall-extension")
run_vscode_command("--list-extensions")

# Final cleanup message
print("\n🚀 Cleanup complete! Restart VS Code to see the changes.")
