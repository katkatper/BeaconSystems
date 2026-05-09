from config.aws_config import get_s3_client

class S3Service:
    def __init__(self, bucket_name):
        self.s3 = get_s3_client()
        self.bucket_name = bucket_name

    # Upload file
    def upload_file(self, file_path, s3_key):
        try:
            self.s3.upload_file(file_path, self.bucket_name, s3_key)
            print(f"Uploaded: {s3_key}")
        except Exception as e:
            print(f" Upload failed: {e}")

    # Download file
    def download_file(self, s3_key, download_path):
        try:
            self.s3.download_file(self.bucket_name, s3_key, download_path)
            print(f" Downloaded: {s3_key}")
        except Exception as e:
            print(f" Download failed: {e}")

    # List files
    def list_files(self):
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name)

            if 'Contents' in response:
                for obj in response['Contents']:
                    print(obj['Key'])
            else:
                print("No files found.")
        except Exception as e:
            print(f" List failed: {e}")

    # Delete file
    def delete_file(self, s3_key):
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            print(f" Deleted: {s3_key}")
        except Exception as e:
            print(f" Delete failed: {e}")
