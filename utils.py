import uuid
import boto3

def upload_to_r2(file_path, bucket_name, endpoint_url,
                 access_key_id, secret_access_key):

    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
    )

    filename = f"{uuid.uuid4()}.png"

    s3.upload_file(
        file_path,
        bucket_name,
        filename,
        ExtraArgs={
            "ContentType": "image/png"
        }
    )

    return filename