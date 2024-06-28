from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import boto3
import os
from dotenv import load_dotenv

def download_file_from_google_drive(file_id, file_name, drive):
    """Download a file from Google Drive given a file ID."""
    file = drive.CreateFile({'id': file_id})
    file.GetContentFile(file_name)
    print(f"Downloaded {file_name} from Google Drive.\n")
    return file_name

def upload_file_to_s3(file_name, bucket_name, s3_key, s3):
    """Upload a file to an S3 bucket."""
    s3.upload_file(file_name, bucket_name, s3_key)
    print(f"Uploaded {file_name} to S3 bucket {bucket_name} with key {s3_key}\n.")

def transfer_file(file_id, file_name, bucket_name, s3_key, drive, s3):
    """Transfer a file from Google Drive to S3."""
    local_file = download_file_from_google_drive(file_id, file_name, drive)
    upload_file_to_s3(local_file, bucket_name, s3_key, s3)
    os.remove(local_file)
    print(f"Deleted local file {local_file} after upload.\n")

def transfer_files_in_folder(folder_id, bucket_name, drive, s3):
    """Transfer all files in a Google Drive folder to an S3 bucket."""
    print(f"Fetching files from folder ID: {folder_id}\n")
    file_list = drive.ListFile({'q': f"'{folder_id}' in parents and trashed=false"}).GetList()

    print(f"Transferring {len(file_list)} files from Google Drive to S3 bucket {bucket_name}.\n")

    for file in file_list:
        file_id = file['id']
        file_name = file['title']
        s3_key = f"{file_name}"  # Define how the S3 key should be named
        transfer_file(file_id, file_name, bucket_name, s3_key, drive, s3)

if __name__ == "__main__":
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    load_dotenv(dotenv_path)  # Load environment variables

    # Replace these variables with your file information and credentials.
    FOLDER_ID = os.getenv('FOLDER_ID')
    BUCKET_NAME = os.getenv('BUCKET_NAME')
    S3_ACCESS_KEY = os.getenv('S3_ACCESS_KEY')
    S3_SECRET_ACCESS_KEY = os.getenv('S3_SECRET_ACCESS_KEY')

    print(f"Folder ID: {FOLDER_ID}\n")
    print(f"Bucket Name: {BUCKET_NAME}\n")

    # Initialize GoogleAuth and GoogleDrive
    gauth = GoogleAuth()

    # Load the client secret file from the config directory
    gauth.LoadClientConfigFile('config/client_secret_288395523855-ol7gukjchfrfmcodq9c4ekq1q93ktrh4.apps.googleusercontent.com.json')

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

    transfer_files_in_folder(FOLDER_ID, BUCKET_NAME, drive, s3)