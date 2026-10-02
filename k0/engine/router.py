from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

INTAKE_CONTRACT = "K0_CENTRAL_INTAKE_V1"
PROFILE_CONTRACT = "K0_PORTAL_PROFILE_V1"
FIVE_FIELDS = ("article_type", "category", "plan_slot", "target_keyword", "title")
PORTAL_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
SHA64_RE = re.compile(r"^[0-9a-f]{64}$")


class Blocked(RuntimeError):
    pass


def _load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise Blocked("JSON_OBJECT_REQUIRED")
    return obj


def validate_intake(intake: dict) -> tuple[str, dict]:
    if intake.get("contract") != INTAKE_CONTRACT:
        raise Blocked("INTAKE_CONTRACT_INVALID")
    if intake.get("publish_allowed") is not False:
        raise Blocked("PUBLISH_ALLOWED_MUST_BE_FALSE")

    portal_key = str(intake.get("portal_key") or "")
    if not PORTAL_RE.fullmatch(portal_key):
        raise Blocked("PORTAL_KEY_INVALID")

    item = intake.get("item")
    if not isinstance(item, dict) or set(item) != set(FIVE_FIELDS):
        raise Blocked("ARTICLE_IDENTITY_NOT_EXACT_FIVE_FIELDS")

    for field in FIVE_FIELDS:
        if not isinstance(item.get(field), str) or not item[field].strip():
            raise Blocked("ARTICLE_FIELD_INVALID:" + field)

    if not SHA64_RE.fullmatch(item["plan_slot"]):
        raise Blocked("PLAN_SLOT_MUST_BE_SHA256")

    return portal_key, item


def load_profile(profiles_dir: Path, portal_key: str) -> dict:
    path = profiles_dir / (portal_key + ".json")
    if not path.is_file():
        raise Blocked("PORTAL_PROFILE_NOT_FOUND:" + portal_key)

    profile = _load(path)
    if profile.get("contract") != PROFILE_CONTRACT:
        raise Blocked("PORTAL_PROFILE_CONTRACT_INVALID")
    if profile.get("portal_key") != portal_key:
        raise Blocked("PORTAL_PROFILE_KEY_MISMATCH")
    if profile.get("active") is not True:
        raise Blocked("PORTAL_PROFILE_INACTIVE")
    if profile.get("publish_allowed") is not False:
        raise Blocked("PORTAL_PROFILE_PUBLISH_BOUNDARY_INVALID")
    if not isinstance(profile.get("allowed_article_types"), list):
        raise Blocked("PORTAL_ALLOWED_TYPES_INVALID")
    return profile


def route(intake: dict, profiles_dir: Path) -> dict:
    portal_key, item = validate_intake(intake)
    profile = load_profile(profiles_dir, portal_key)

    if item["article_type"] not in profile["allowed_article_types"]:
        raise Blocked("ARTICLE_TYPE_NOT_ALLOWED_FOR_PORTAL")

    identity_core = {
        "portal_key": portal_key,
        **{key: item[key] for key in FIVE_FIELDS},
    }
    identity_sha256 = hashlib.sha256(
        json.dumps(identity_core, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return {
        "contract": "K0_ROUTE_RECEIPT_V1",
        "status": "READY_FOR_K0_PRODUCTION",
        "portal_key": portal_key,
        "profile_contract": profile["contract"],
        "profile_display_name": profile["display_name"],
        "article_identity": item,
        "job_identity_sha256": identity_sha256,
        "production_stages": [
            "RESEARCH",
            "WRITE",
            "TEXT_RULES",
            "LANGUAGE",
            "FACT_BINDING",
            "PORTAL_BINDING",
            "FINALIZE",
        ],
        "publish_allowed": False,
    }


def route_file(intake_path: str, profiles_dir: str) -> dict:
    return route(_load(Path(intake_path)), Path(profiles_dir))
