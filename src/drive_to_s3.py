from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import boto3
import os

# Authenticate and create the PyDrive client.
gauth = GoogleAuth()
gauth.LocalWebserverAuth()  # Creates local webserver and automatically handles authentication.
drive = GoogleDrive(gauth)

# S3 client
s3 = boto3.client('s3')

def download_file_from_google_drive(file_id, file_name):
    """Download a file from Google Drive given a file ID."""
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(file_name)
    print(f"Downloaded {file_name} from Google Drive.")
    return file_name

def upload_file_to_s3(file_name, bucket_name, s3_key):
    """Upload a file to an S3 bucket."""
    s3.upload_file(file_name, bucket_name, s3_key)
    print(f"Uploaded {file_name} to S3 bucket {bucket_name} with key {s3_key}.")

def transfer_file(file_id, file_name, bucket_name, s3_key):
    """Transfer a file from Google Drive to S3."""
    local_file = download_file_from_google_drive(file_id, file_name)
    upload_file_to_s3(local_file, bucket_name, s3_key)
    os.remove(local_file)
    print(f"Deleted local file {local_file} after upload.")

# Replace these variables with your file information and credentials.
FILE_ID = 'your-google-drive-file-id'
FILE_NAME = 'your-local-file-name'
BUCKET_NAME = 'your-s3-bucket-name'
S3_KEY = 'your-s3-key'

transfer_file(FILE_ID, FILE_NAME, BUCKET_NAME, S3_KEY)