#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POLICY = ROOT / "START_POLICY.json"
PROJECTS = ROOT / "projects"

class Blocked(RuntimeError):
    pass

def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Blocked("JSON_OBJECT_REQUIRED")
    return value

def authorize(project_id: str) -> dict:
    policy = load(POLICY)
    if policy.get("contract") != "TEXT_START_CENTRAL_V1":
        raise Blocked("POLICY_CONTRACT_INVALID")
    if policy.get("mode") != "START_ONLY":
        raise Blocked("POLICY_MODE_INVALID")
    if any(policy.get(k) is not False for k in (
        "free_target_selection",
        "free_command_selection",
        "free_branch_selection",
    )):
        raise Blocked("FREE_SELECTION_FORBIDDEN")
    if any(policy.get(k) != "NONE" for k in (
        "production_logic_authority",
        "article_content_authority",
        "quality_rule_authority",
        "publish_authority",
    )):
        raise Blocked("START_REPO_AUTHORITY_TOO_BROAD")

    allowed = policy.get("allowed_projects")
    if not isinstance(allowed, list) or project_id not in allowed:
        raise Blocked("PROJECT_NOT_ALLOWED")

    project_path = PROJECTS / f"{project_id}.json"
    if not project_path.is_file():
        raise Blocked("PROJECT_BINDING_MISSING")
    project = load(project_path)

    expected = {
        "contract": "TEXT_START_PROJECT_V1",
        "project_id": project_id,
        "start_mode": "FIXED_SINGLE_START",
        "free_parameters": False,
        "article_content_rules_changed": False,
        "quality_rules_changed": False,
        "production_logic_changed": False,
        "publish_allowed": False,
    }
    for key, value in expected.items():
        if project.get(key) != value:
            raise Blocked("PROJECT_BINDING_INVALID:" + key)

    target_repository = str(project.get("target_repository") or "")
    target_ref = str(project.get("target_ref") or "")
    target_workflow = str(project.get("target_workflow") or "")
    command = str(project.get("canonical_start_command") or "")
    if not target_repository or not target_ref or not target_workflow or not command:
        raise Blocked("PROJECT_TARGET_INCOMPLETE")

    if project_id == "pferdeatelier":
        if target_repository != "hallo-netizen/affiliate-pferdeportal":
            raise Blocked("PFERDEATELIER_REPOSITORY_DRIFT")
        if target_ref != "main":
            raise Blocked("PFERDEATELIER_REF_DRIFT")
        if target_workflow != "text-start-pferdeatelier.yml":
            raise Blocked("PFERDEATELIER_WORKFLOW_DRIFT")
        if command != "python3 isolated_system4/parent_start.py start-current-bound":
            raise Blocked("PFERDEATELIER_COMMAND_DRIFT")

    return {
        "contract": "TEXT_START_AUTHORIZATION_V1",
        "status": "START_AUTHORIZED",
        "project_id": project_id,
        "target_repository": target_repository,
        "target_ref": target_ref,
        "target_workflow": target_workflow,
        "canonical_start_command": command,
        "free_parameters": False,
        "production_logic_authority": "NONE",
        "article_content_authority": "NONE",
        "quality_rule_authority": "NONE",
        "publish_authority": "NONE",
    }

def main(argv: list[str]) -> int:
    try:
        if len(argv) != 3 or argv[1] != "start":
            raise Blocked("USE: start.py start PROJECT_ID")
        print(json.dumps(authorize(argv[2]), ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({
            "ok": False,
            "status": "START_BLOCKED",
            "reason": str(exc),
        }, ensure_ascii=False, sort_keys=True))
        return 2

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
