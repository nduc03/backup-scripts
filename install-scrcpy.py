import os
import requests
import zipfile
import tempfile
import shutil
import sys
from packaging import version

# --- CONFIGURATION ---
# IMPORTANT: Specify the full path where scrcpy should be installed.
# Example: r"C:\Tools\scrcpy"
DEST_PATH = r"YOUR_DEST_PATH_HERE"
# ---------------------

GITHUB_API_URL = "https://api.github.com/repos/Genymobile/scrcpy/releases/latest"


def has_new_ver(online: str | None, local: str | None) -> bool:
    return False if online is None else True if local is None else version.parse(online[1:]) > version.parse(local[1:])


def get_latest_tag():
    """
    Fetches the latest release tag from the scrcpy GitHub repository.
    """
    try:
        print("Fetching latest release information...")
        response = requests.get(GITHUB_API_URL, timeout=10)
        response.raise_for_status()  # Raise an error for bad status codes

        data = response.json()
        latest_tag = data.get("tag_name")

        if not latest_tag:
            print("Error: Could not find 'tag_name' in API response.")
            return None

        print(f"Latest tag found: {latest_tag}")
        return latest_tag

    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest release: {e}")
        return None

def get_current_version(version_file):
    """
    Reads the currently installed version from the version file.
    """
    if not os.path.exists(version_file):
        print("No local version file found.")
        return None

    try:
        with open(version_file, 'r', encoding='utf-8') as f:
            current_tag = f.read().strip()
            print(f"Current local version: {current_tag}")
            return current_tag
    except IOError as e:
        print(f"Error reading version file: {e}")
        return None


def download_and_extract(tag, temp_dir):
    """
    Downloads and extracts the specified release tag to a temp directory.
    Returns the path to the extracted contents.
    """
    download_url = f"https://github.com/Genymobile/scrcpy/releases/latest/download/scrcpy-win64-{tag}.zip"

    try:
        print(f"Downloading: {download_url}")
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()

        zip_path = os.path.join(temp_dir, "scrcpy.zip")

        with open(zip_path, 'wb') as f:
            shutil.copyfileobj(response.raw, f)

        print("Download complete. Extracting files...")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Get the name of the root folder inside the zip
            if not zip_ref.namelist():
                print("Error: Zip file is empty.")
                return None

            # e.g., "scrcpy-win64-v2.4.0/"
            root_folder_in_zip = zip_ref.namelist()[0].split('/')[0]
            extract_path = os.path.join(temp_dir, "extracted")
            zip_ref.extractall(extract_path)

            source_dir = os.path.join(extract_path, root_folder_in_zip)

            if not os.path.isdir(source_dir):
                print(f"Error: Could not find expected directory '{root_folder_in_zip}' after extraction.")
                return None

            print(f"Extracted to: {source_dir}")
            return source_dir

    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return None
    except zipfile.BadZipFile:
        print("Error: Downloaded file is not a valid zip file.")
        return None
    except Exception as e:
        print(f"An error occurred during download/extraction: {e}")
        return None

def copy_files(source_dir, dest_dir):
    print(f"Cleaning destination directory: {dest_dir}...")
    if not os.path.exists(dest_dir):
        raise FileNotFoundError("Destination folder does not exists.")
    else:
        # --- 3. Clean all old files, no exceptions ---
        for item in os.listdir(dest_dir):
            item_path = os.path.join(dest_dir, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                print(f"Warning: Could not delete {item_path}: {e}")

    print(f"Copying files from {source_dir} to {dest_dir}...")

    # --- 4. Copy new files, no exceptions ---
    for item in os.listdir(source_dir):
        source_item_path = os.path.join(source_dir, item)
        dest_item_path = os.path.join(dest_dir, item)

        try:
            if os.path.isdir(source_item_path):
                shutil.copytree(source_item_path, dest_item_path, dirs_exist_ok=True)
            else:
                shutil.copy2(source_item_path, dest_item_path)
        except Exception as e:
            print(f"Error copying {item}: {e}")

    print("File copy complete.")

def update_version_file(version_file, new_tag):
    """
    Creates or overwrites the version file with the new tag.
    """
    try:
        with open(version_file, 'w', encoding='utf-8') as f:
            f.write(new_tag)
        print(f"Updated version file to: {new_tag}")
    except IOError as e:
        print(f"Error writing version file: {e}")

def main():
    if DEST_PATH == r"YOUR_DEST_PATH_HERE":
        print("Error: Please set the 'DEST_PATH' variable at the top of the script.")
        sys.exit(1)

    version_file_path = os.path.join(DEST_PATH, "version")

    latest_tag = get_latest_tag()
    if not latest_tag:
        sys.exit(1)

    current_tag = get_current_version(version_file_path)

    new_ver = has_new_ver(latest_tag, current_tag)

    if not new_ver:
        print(f"scrcpy is already up to date (Version: {current_tag}).")
        sys.exit(0)


    print(f"New version available: {latest_tag}. Starting update...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            print(f"Created temporary directory: {temp_dir}")

            source_dir = download_and_extract(latest_tag, temp_dir)
            if not source_dir:
                print("Update failed during download/extraction.")
                sys.exit(1)

            copy_files(source_dir, DEST_PATH)

            update_version_file(version_file_path, latest_tag)

            print("\nscrcpy update successful!")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
