from __future__ import annotations

import ast
from pathlib import Path

K0_ROOT = Path(__file__).resolve().parents[1]
ENGINE_ROOT = K0_ROOT / "engine"

FORBIDDEN_RUNTIME_TOKENS = (
    "affiliate-pferdeportal",
    "concept_agent/",
    "control/startmaster",
    "real_runs/production",
    "konzept9/",
    "konzept10/",
)

ALLOWED_IMPORT_ROOTS = {
    "__future__",
    "ast",
    "hashlib",
    "html",
    "json",
    "pathlib",
    "re",
    "sys",
    "unittest",
}


class IsolationError(RuntimeError):
    pass


def check() -> dict:
    findings = []

    for path in K0_ROOT.rglob("*"):
        if path.is_symlink():
            findings.append("SYMLINK_FORBIDDEN:" + str(path.relative_to(K0_ROOT)))

    for path in ENGINE_ROOT.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(K0_ROOT))
        # The guard itself contains the deny-list by definition; scan every other runtime module.
        scan_runtime_tokens = path.name != "isolation_guard.py"
        for token in FORBIDDEN_RUNTIME_TOKENS if scan_runtime_tokens else ():
            if token in text:
                findings.append("FORBIDDEN_RUNTIME_REFERENCE:" + rel + ":" + token)

        tree = ast.parse(text, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".", 1)[0]
                    if root not in ALLOWED_IMPORT_ROOTS and root != "k0":
                        findings.append("IMPORT_OUTSIDE_K0:" + rel + ":" + alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    continue
                root = module.split(".", 1)[0]
                if root and root not in ALLOWED_IMPORT_ROOTS and root != "k0":
                    findings.append("IMPORT_OUTSIDE_K0:" + rel + ":" + module)

    if findings:
        raise IsolationError(";".join(findings))

    return {
        "contract": "K0_ISOLATION_RECEIPT_V1",
        "status": "PASS",
        "symlinks": "NONE",
        "external_runtime_references": "NONE",
        "imports_outside_k0_or_stdlib": "NONE",
        "publish_allowed": False,
    }
