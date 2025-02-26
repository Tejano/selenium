import os
import shutil
import json

# Get the user's home directory
home_dir = os.path.expanduser("~")

# Define VS Code paths
vscode_paths = {
    "Windows": {
        "extensions": os.path.join(home_dir, "AppData", "Roaming", "Code", "extensions"),
        "cached_extensions": os.path.join(home_dir, "AppData", "Roaming", "Code", "CachedExtensions"),
        "global_storage": os.path.join(home_dir, "AppData", "Roaming", "Code", "User", "globalStorage"),
        "extensions_json": os.path.join(home_dir, "AppData", "Roaming", "Code", "User", "extensions.json"),
    },
    "Mac/Linux": {
        "extensions": os.path.join(home_dir, ".vscode", "extensions"),
        "cached_extensions": os.path.join(home_dir, ".config", "Code", "CachedExtensions"),
        "global_storage": os.path.join(home_dir, ".config", "Code", "User", "globalStorage"),
        "extensions_json": os.path.join(home_dir, ".config", "Code", "User", "extensions.json"),
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

# Remove extension folders
for key, path in os_paths.items():
    if "extensions" in key:
        extension_path = os.path.join(path, extension_name)
        remove_directory(extension_path)

# Remove cached extension data
remove_directory(os_paths["cached_extensions"])

# Remove global storage data (if necessary)
remove_directory(os_paths["global_storage"])

# Remove extension entry from `extensions.json`
extensions_json_path = os_paths["extensions_json"]
if os.path.exists(extensions_json_path):
    try:
        with open(extensions_json_path, "r", encoding="utf-8") as file:
            extensions_data = json.load(file)

        if isinstance(extensions_data, list):  # Some versions store extensions as a list
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

print("\n🚀 Cleanup complete! Restart VS Code to see the changes.")
