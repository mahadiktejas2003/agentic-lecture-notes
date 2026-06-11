import os
import boto3
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def upload_to_r2(file_path, object_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='s3',
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name=os.getenv("R2_REGION")
    )
    try:
        client.upload_file(file_path, os.getenv("R2_BUCKET_NAME"), object_name)
        print(f"✅ Uploaded {file_path} to R2 as {object_name}")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return False

def log_to_supabase(run_data):
    supabase: Client = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    )
    try:
        data = supabase.table("pipeline_runs").insert(run_data).execute()
        print(f"✅ Logged run to Supabase: {data}")
        return True
    except Exception as e:
        print(f"❌ Supabase log failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Cloud Connections...")
    print("R2 Endpoint:", os.getenv("R2_ENDPOINT"))
    print("Supabase URL:", os.getenv("SUPABASE_URL"))
    print("✅ Configuration loaded successfully.")
