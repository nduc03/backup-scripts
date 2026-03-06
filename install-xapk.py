# same with install-xapk-bundle.py but for older xapk format.
import sys
import subprocess
import zipfile
import tempfile
from pathlib import Path

def check_adb_exists():
    try:
        subprocess.run(['adb', 'version'], check=True, capture_output=True)
        return True
    except FileNotFoundError:
        print("Error: adb is not installed or not found in PATH.")
        return False
    except subprocess.CalledProcessError:
        print("Error: adb command failed.")
        return False

def check_device_connected():
    try:
        result = subprocess.run(
            ['adb', 'devices'], check=True, capture_output=True, text=True
        )
        devices = result.stdout.strip().split('\n')[1:]

        if not any(device.strip() for device in devices):
            print("Error: No devices connected.")
            return False

        return True
    except subprocess.CalledProcessError:
        print("Error: Failed to check connected devices.")
        return False

def main(argv=None):
    if len(argv) < 2:
        print("Syntax: iax <path_to_xapk_file>")
        sys.exit(1)

    xapk_file = Path(sys.argv[1])

    if not xapk_file.is_file():
        print(f"Error: File '{str(xapk_file)}' does not exist.")
        sys.exit(1)

    if not check_adb_exists():
        sys.exit(1)

    if not check_device_connected():
        sys.exit(1)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            with zipfile.ZipFile(xapk_file, 'r') as zip_archive:
                zip_archive.extractall(temp_dir)
        except zipfile.BadZipFile:
            print("Error: Failed to unpack the .xapk file (bad zip file).")
            sys.exit(1)

        temp_path = Path(temp_dir)

        apk_path = next(temp_path.rglob("*.apk"), None)

        obb_dir_path = temp_path / "Android" / "obb"

        obb_file_path = next(obb_dir_path.glob("*/*.obb"), None)

        package_name = obb_file_path.parent.name if obb_file_path else None


        if apk_path:
            print(f"Installing {apk_path.name} to device...")

            install_result = subprocess.run(
                ['adb', 'install', str(apk_path)],
                shell=True,
                capture_output=True,
                check=False,
                text=True
            )

            if install_result.returncode == 0:
                print(install_result.stdout)
            else:
                print(install_result.stderr)
                print("Error: Failed to install APKs.")
                sys.exit(1)
        else:
            print("Error: No APK files found in the extracted .xapk package.")
            sys.exit(1)


        if obb_file_path and obb_file_path.is_file():
            obb_destination = f"/sdcard/Android/obb/{package_name}"

            try:
                print('Delete old OBB file...')

                delete_result = subprocess.run(['adb', 'shell', 'rm', '-r', f'{obb_destination}/*'],check=False, capture_output=True)

                if delete_result.returncode != 0:
                    print(f"Warning: Failed to delete old OBB files (code: {delete_result.returncode}). This may due to OBB does not exist. Continuing to copy new OBB.")
                else:
                    print("Old OBB files deleted successfully.")

                print(f"Copying OBB file {obb_file_path.name} to device...")
                subprocess.run(['adb', 'push', str(obb_file_path), obb_destination], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: Failed to copy OBB file: {e}")
                sys.exit(1)
            print(f"OBB file copied to {obb_destination}")
        else:
            print("Warning: No OBB files found in the extracted .xapk package. Skipping OBB installation.")
            sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
