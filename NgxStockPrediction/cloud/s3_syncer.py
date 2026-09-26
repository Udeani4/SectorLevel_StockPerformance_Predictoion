import os
import subprocess

class S3Sync:
    def sync_folder_to_s3(self, folder, aws_bucket_url):
        command = ["aws", "s3", "sync", folder, aws_bucket_url]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"AWS S3 sync failed: {result.stderr}")

    def sync_folder_from_s3(self, folder, aws_bucket_url):
        command = ["aws", "s3", "sync", aws_bucket_url, folder]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"AWS S3 sync failed: {result.stderr}")