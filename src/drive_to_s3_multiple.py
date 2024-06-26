from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import boto3
import os
from dotenv import load_dotenv


def download_file_from_google_drive(file_id, file_name, drive):
    """Download a file from Google Drive given a file ID."""
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(file_name)
    print(f"Downloaded {file_name} from Google Drive.")
    return file_name

def upload_file_to_s3(file_name, bucket_name, s3_key, s3):
    """Upload a file to an S3 bucket."""
    s3.upload_file(file_name, bucket_name, s3_key)
    print(f"Uploaded {file_name} to S3 bucket {bucket_name} with key {s3_key}.")

def transfer_file(file_id, file_name, bucket_name, s3_key, drive, s3):
    """Transfer a file from Google Drive to S3."""
    local_file = download_file_from_google_drive(file_id, file_name, drive)
    upload_file_to_s3(local_file, bucket_name, s3_key, s3)
    os.remove(local_file)
    print(f"Deleted local file {local_file} after upload.")

def transfer_files_in_folder(folder_id, bucket_name, drive, s3):
    """Transfer all files in a Google Drive folder to an S3 bucket."""
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()
    for file in file_list:
        file_id = file['id']
        file_name = file['title']
        s3_key = f"{file_name}"  # Define how the S3 key should be named
        transfer_file(file_id, file_name, bucket_name, s3_key, drive, s3)

if __name__ == "__main__":
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)  # Load environment variables

    # Replace these variables with your file information and credentials.
    FOLDER_ID = os.getenv('your-google-drive-folder-id')
    BUCKET_NAME = os.getenv('your-s3-bucket-name')
    S3_ACCESS_KEY = os.getenv('your-s3-key')
    S3_SECRET_ACCESS_KEY = os.getenv('your-s3-secret-key')

    # Authenticate and create the PyDrive client.
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # Creates local webserver and automatically handles authentication.
    drive = GoogleDrive(gauth)

    # S3 client
    s3 = boto3.client(
        's3',
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY
    )

    transfer_files_in_folder(FOLDER_ID, BUCKET_NAME, drive, s3)
