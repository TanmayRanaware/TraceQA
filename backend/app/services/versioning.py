import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional


VERSIONS_DIR = os.environ.get("REQ_VERSIONS_DIR", "/Users/spartan/Documents/enterprise-requirements-ai/req_versions")
os.makedirs(VERSIONS_DIR, exist_ok=True)


def _journey_dir(journey: str) -> str:
	safe = hashlib.sha256(journey.encode()).hexdigest()[:16]
	d = os.path.join(VERSIONS_DIR, f"{safe}__{journey}")
	os.makedirs(d, exist_ok=True)
	return d


def _timeline_path(journey: str) -> str:
	return os.path.join(_journey_dir(journey), "timeline.jsonl")


def record_version(journey: str, source_type: str, document_uri: str, summary: str = "", effective_date: Optional[str] = None) -> str:
	ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
	version_id = f"{ts}-{source_type}"
	entry = {
		"version": version_id,
		"journey": journey,
		"source_type": source_type,
		"document_uri": document_uri,
		"summary": summary,
		"effective_date": effective_date,
		"created_at": ts,
	}
	with open(_timeline_path(journey), "a", encoding="utf-8") as f:
		f.write(json.dumps(entry, ensure_ascii=False) + "\n")
	return version_id


def list_versions(journey: Optional[str] = None) -> List[Dict]:
	if journey is None:
		journeys = []
		for name in os.listdir(VERSIONS_DIR):
			if "__" in name:
				journeys.append(name.split("__", 1)[1])
		return [{"journey": j} for j in sorted(journeys)]
	path = _timeline_path(journey)
	if not os.path.exists(path):
		return []
	with open(path, "r", encoding="utf-8") as f:
		return [json.loads(line) for line in f]


def load_version_text(document_uri: str) -> str:
	try:
		with open(document_uri, "r", encoding="utf-8", errors="ignore") as f:
			return f.read()
	except Exception:
		try:
			with open(document_uri, "rb") as f:
				return f.read().decode("utf-8", errors="ignore")
		except Exception:
			return ""


def diff_versions(journey: str, from_version: str, to_version: str) -> Dict:
	versions = list_versions(journey)
	m = {v["version"]: v for v in versions}
	a = m.get(from_version)
	b = m.get(to_version)
	if not a or not b:
		return {"added": [], "removed": [], "changed": []}
	text_a = load_version_text(a["document_uri"]).splitlines()
	text_b = load_version_text(b["document_uri"]).splitlines()
	set_a = set(text_a)
	set_b = set(text_b)
	added = list(set_b - set_a)
	removed = list(set_a - set_b)
	changed = [line for line in set_a & set_b if line not in text_a or line not in text_b]
	return {"added": added, "removed": removed, "changed": changed}
