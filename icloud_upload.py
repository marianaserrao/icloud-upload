from icloudpy import ICloudPyService
from tqdm import tqdm
import sys
import os


class ICloudUpload:
    def __init__(self, local_root, remote_root, log_file, username, password):
        self.local_root = local_root
        self.remote_root = remote_root
        self.username = username
        self.password = password

        print('Authenticating...')
        self.api = self.get_api()

        print('Scaning directory...')
        self.total_files = self.count_files(local_root)
        print(f'{self.total_files} files found')

        log = open(log_file, 'a+')
        log.seek(0)
        self.log = log
        self.uploaded_files = log.read().split('\n')
        self.uploaded_files.remove('')
        print(f'{len(self.uploaded_files)} uploaded files')

        self.make_remote_dir(remote_root)

        self.current_local_folder = local_root
        self.current_remote_folder = remote_root

    def get_api(self):
        api = ICloudPyService(self.username, self.password)
        if api.requires_2fa:
            print("Two-factor authentication required.")
            code = input(
                "Enter the code you received of one of your approved devices: ")
            result = api.validate_2fa_code(code)
            print("Code validation result: %s" % result)

            if not result:
                print("Failed to verify security code")
                sys.exit(1)

            if not api.is_trusted_session:
                print("Session is not trusted. Requesting trust...")
                result = api.trust_session()
                print("Session trust result %s" % result)

                if not result:
                    print(
                        "Failed to request trust. You will likely be prompted for the code again in the coming weeks")
        elif api.requires_2sa:
            import click
            print("Two-step authentication required. Your trusted devices are:")

            devices = api.trusted_devices
            for i, device in enumerate(devices):
                print("  %s: %s" % (i, device.get('deviceName',
                                                  "SMS to %s" % device.get('phoneNumber'))))

            device = click.prompt(
                'Which device would you like to use?', default=0)
            device = devices[device]
            if not api.send_verification_code(device):
                print("Failed to send verification code")
                sys.exit(1)

            code = click.prompt('Please enter validation code')
            if not api.validate_verification_code(device, code):
                print("Failed to verify verification code")
                sys.exit(1)
        api.drive
        api._drive.params["clientId"] = api.client_id
        return api

    def make_remote_dir(self, path):
        self.api.drive.mkdir(path)
        self.api = self.get_api()

    def get_drive_folder(self, path):
        folders = path.split('/')
        current_folder = self.api.drive
        for f in folders:
            current_folder = current_folder[f]
        return current_folder

    def count_files(self, directory):
        file_count = 0
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_file():
                    file_count += 1
                elif entry.is_dir():
                    file_count += self.count_files(entry.path)
        return file_count

    def upload_to_path(self, local_path, remote_path, pbar):
        if os.path.isdir(local_path):
            # Create the remote directory if it doesn't exist
            self.make_remote_dir(remote_path)

            # Separate files and subfolders
            files_to_upload = []
            subfolders = []
            with os.scandir(local_path) as entries:
                for entry in entries:
                    if entry.is_file():
                        files_to_upload.append(entry)
                    elif entry.is_dir():
                        subfolders.append(entry)

            # Upload files in the current directory
            remote_folder = self.get_drive_folder(remote_path)
            for file_entry in files_to_upload:
                pbar.set_description(f"Uploading {file_entry.name}")
                if file_entry.path not in self.uploaded_files:
                    with open(file_entry, 'rb') as file_in:
                        remote_folder.upload(file_in)
                    self.log.write(f'{file_entry.path}\n')
                pbar.update(1)

            # Recursively upload subfolders
            for subfolder_entry in subfolders:
                self.upload_to_path(subfolder_entry.path, os.path.join(
                    remote_path, subfolder_entry.name), pbar)

    def upload(self):
        with tqdm(total=self.total_files) as pbar:
            self.upload_to_path(self.local_root, self.remote_root, pbar)
