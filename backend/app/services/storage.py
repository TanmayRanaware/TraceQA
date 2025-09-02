import os
import hashlib
from datetime import datetime

BASE_DIR = os.environ.get("OBJECT_STORE", "/Users/spartan/Documents/enterprise-requirements-ai/object_store")
os.makedirs(BASE_DIR, exist_ok=True)

def save_object(content: bytes, filename: str) -> str:
	digest = hashlib.sha256(content).hexdigest()[:16]
	dir_path = os.path.join(BASE_DIR, datetime.utcnow().strftime("%Y/%m/%d"))
	os.makedirs(dir_path, exist_ok=True)
	path = os.path.join(dir_path, f"{digest}__{filename}")
	with open(path, "wb") as f:
		f.write(content)
	return path
