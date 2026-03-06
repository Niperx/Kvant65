#!/usr/bin/env python
"""
Однократная загрузка папки media/ в S3 (префикс media/ в бакете).
Запуск локально, после экспорта БД. Требует: boto3, переменные AWS_* в окружении.

Пример (PowerShell):
  $env:AWS_ACCESS_KEY_ID="..."
  $env:AWS_SECRET_ACCESS_KEY="..."
  $env:AWS_STORAGE_BUCKET_NAME="your-bucket"
  $env:AWS_S3_REGION_NAME="us-east-1"
  python upload_media_to_s3.py
"""
import os
import sys
from pathlib import Path

try:
    import boto3
except ImportError:
    print("Установите boto3: pip install boto3")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent
MEDIA_ROOT = BASE_DIR / "media"
BUCKET = os.environ.get("AWS_STORAGE_BUCKET_NAME")
REGION = os.environ.get("AWS_S3_REGION_NAME", "us-east-1")
PREFIX = "media"

def main():
    if not BUCKET:
        print("Задайте AWS_STORAGE_BUCKET_NAME в окружении.")
        sys.exit(1)
    if not MEDIA_ROOT.is_dir():
        print(f"Папка {MEDIA_ROOT} не найдена.")
        sys.exit(1)

    session = boto3.Session(
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        region_name=REGION,
    )
    s3 = session.client("s3")
    uploaded = 0
    for path in MEDIA_ROOT.rglob("*"):
        if path.is_file():
            key = f"{PREFIX}/{path.relative_to(MEDIA_ROOT).as_posix()}"
            try:
                s3.upload_file(str(path), BUCKET, key, ExtraArgs={"ACL": "public-read"})
                uploaded += 1
                print(key)
            except Exception as e:
                print(f"Ошибка {key}: {e}", file=sys.stderr)
    print(f"\nЗагружено файлов: {uploaded}")

if __name__ == "__main__":
    main()
