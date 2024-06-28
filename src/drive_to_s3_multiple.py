from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import boto3
import os
from dotenv import load_dotenv

def download_file_from_google_drive(file_id, file_name, mime_type, drive, allowed_types):
    """Download a file from Google Drive given a file ID."""
    if not any(file_name.lower().endswith(allowed_type.lower()) for allowed_type in allowed_types):
        print(f"Skipping file {file_name} as it does not match the allowed types {allowed_types}\n")
        return None

    file = drive.CreateFile({'id': file_id})
    
    if 'downloadUrl' in file or mime_type.startswith('image/'):
        file.GetContentFile(file_name)
    elif mime_type == 'application/vnd.google-apps.document':
        file.GetContentFile(file_name, mimetype='application/pdf')
    elif mime_type == 'application/vnd.google-apps.spreadsheet':
        file.GetContentFile(file_name, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    elif mime_type == 'application/vnd.google-apps.presentation':
        file.GetContentFile(file_name, mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
    else:
        print(f"Cannot download file with MIME type {mime_type}\n")
        return None
    
    print(f"Downloaded {file_name} from Google Drive.\n")
    return file_name

def upload_file_to_s3(file_name, s3_bucket_name, s3_key, s3):
    """Upload a file to an S3 bucket."""
    s3.upload_file(file_name, s3_bucket_name, s3_key)
    print(f"Uploaded {file_name} to S3 bucket {s3_bucket_name} with key {s3_key}\n.")

def transfer_file(file_id, file_name, mime_type, s3_bucket_name, s3_key, drive, s3, allowed_types):
    """Transfer a file from Google Drive to S3."""
    local_file = download_file_from_google_drive(file_id, file_name, mime_type, drive, allowed_types)
    if local_file:
        upload_file_to_s3(local_file, s3_bucket_name, s3_key, s3)
        os.remove(local_file)
        print(f"Deleted local file {local_file} after upload.\n")

def transfer_files_in_folder(drive_folder_id, s3_bucket_name, s3_folder_prefix, drive, s3, allowed_types):
    """Transfer all files in a Google Drive folder to an S3 bucket."""
    print(f"Fetching files from folder ID: {drive_folder_id}\n")
    file_list = drive.ListFile({'q': f"'{drive_folder_id}' in parents and trashed=false"}).GetList()

    print(f"Transferring {len(file_list)} files from Google Drive to S3 bucket {s3_bucket_name}.\n")

    for file in file_list:
        file_id = file['id']
        file_name = file['title']
        mime_type = file['mimeType']
        s3_key = f"{s3_folder_prefix}/{file_name}"  # Define how the S3 key should be named
        transfer_file(file_id, file_name, mime_type, s3_bucket_name, s3_key, drive, s3, allowed_types)

if __name__ == "__main__":
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)  # Load environment variables

    # Replace these variables with your file information and credentials.
    DRIVE_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')
    S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
    S3_FOLDER_PREFIX = os.getenv('S3_FOLDER_PREFIX')  # e.g., 'test-folder'
    S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
    S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')
    GOOGLE_SECRET_PATH = os.getenv('GOOGLE_SECRET_PATH')
    ALLOWED_TYPES = os.getenv('ALLOWED_TYPES').split(',')  # e.g., 'jpg,png,pdf'

    print(f"Folder ID: {DRIVE_FOLDER_ID}\n")
    print(f"S3 Bucket Name: {S3_BUCKET_NAME}\n")
    print(f"S3 Folder Prefix: {S3_FOLDER_PREFIX}\n")
    print(f"Allowed File Types: {ALLOWED_TYPES}\n")

    # Initialize GoogleAuth and GoogleDrive
    gauth = GoogleAuth()

    # Load the client secret file from the config directory
    gauth.LoadClientConfigFile(GOOGLE_SECRET_PATH)

    # Try to load saved client credentials
    gauth.LoadCredentialsFile("config/mycreds.txt")

    if gauth.credentials is None:
        # Authenticate if credentials are not there
        gauth.LocalWebserverAuth()
    elif gauth.access_token_expired:
        # Refresh them if expired
        gauth.Refresh()
    else:
        # Initialize the saved creds
        gauth.Authorize()

    # Save the current credentials to a file in the config directory
    gauth.SaveCredentialsFile("config/mycreds.txt")

    drive = GoogleDrive(gauth)

    # S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY
    )

    transfer_files_in_folder(DRIVE_FOLDER_ID, S3_BUCKET_NAME, S3_FOLDER_PREFIX, drive, s3, ALLOWED_TYPES)