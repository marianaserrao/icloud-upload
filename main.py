from icloud_upload import ICloudUpload
import yaml
import getpass

local_directory = "teste"
remote_directory = "Fotos"
log_file = 'uploaded.log'

with open('auth.yaml') as f:
    auth = yaml.safe_load(f)

icloud_username = auth['username']
icloud_password = getpass.getpass("Enter your iCloud password: ")


def main():
    icloudUpload = ICloudUpload(
        local_directory, remote_directory, log_file, icloud_username, icloud_password)
    icloudUpload.upload()
    icloudUpload.log.close()


if __name__ == '__main__':
    main()
