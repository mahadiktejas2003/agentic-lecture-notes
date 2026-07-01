import os
import time
import boto3
from boto3.s3.transfer import TransferConfig
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def check_env_vars():
    required = ["R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_REGION", "R2_BUCKET_NAME", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

def check_r2_env_vars():
    required = ["R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_REGION", "R2_BUCKET_NAME"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required R2 environment variables: {', '.join(missing)}")

def check_supabase_env_vars():
    required = ["SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise ValueError(f"Missing required Supabase environment variables: {', '.join(missing)}")

def upload_to_r2(file_path, object_name):
    check_r2_env_vars()
    session = boto3.session.Session()
    client = session.client(
        service_name='s3',
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name=os.getenv("R2_REGION")
    )
    config = TransferConfig(multipart_threshold=512 * 1024 * 1024)
    try:
        client.upload_file(file_path, os.getenv("R2_BUCKET_NAME"), object_name, Config=config)
        print(f"✅ Uploaded {file_path} to R2 as {object_name}")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def log_to_supabase(run_data):
    check_supabase_env_vars()
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    last_error = None
    for attempt in range(1, 4):
        try:
            data = supabase.table("pipeline_runs").upsert(run_data).execute()
            print(f"✅ Logged run to Supabase: {data}")
            return True
        except Exception as e:
            last_error = e
            print(f"⚠️ Supabase log attempt {attempt}/3 failed: {e}")
            if attempt < 3:
                time.sleep(2 ** (attempt - 1))
    print(f"❌ Supabase log failed after retries: {last_error}")
    return False

if __name__ == "__main__":
    check_env_vars()
    print("Testing Cloud Connections...")
    print("R2 Endpoint:", os.getenv("R2_ENDPOINT"))
    print("Supabase URL:", os.getenv("SUPABASE_URL"))
    print("✅ Configuration loaded successfully.")
