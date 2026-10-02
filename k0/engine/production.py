from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from pathlib import Path

from .router import Blocked, FIVE_FIELDS, load_profile, route

RESEARCH_CONTRACT = "K0_RESEARCH_V1"
ARTICLE_CONTRACT = "K0_ARTICLE_V1"
FINAL_CONTRACT = "K0_FINAL_ARTICLE_V1"


def _load(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise Blocked("JSON_OBJECT_REQUIRED:" + str(path))
    return obj


def _save(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha_text(value: str) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def _visible(value: str) -> str:
    text = re.sub(r"(?is)<script\b.*?</script>|<style\b.*?</style>", " ", str(value or ""))
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _words(value: str) -> list[str]:
    return re.findall(r"\b[\wÄÖÜäöüß-]+\b", _visible(value), re.UNICODE)


def validate_research(research: dict, item: dict, portal_key: str) -> dict[str, dict]:
    if research.get("contract") != RESEARCH_CONTRACT:
        raise Blocked("RESEARCH_CONTRACT_INVALID")
    if research.get("portal_key") != portal_key:
        raise Blocked("RESEARCH_PORTAL_MISMATCH")
    if research.get("plan_slot") != item["plan_slot"]:
        raise Blocked("RESEARCH_PLAN_SLOT_MISMATCH")
    if research.get("publish_allowed") is not False:
        raise Blocked("RESEARCH_PUBLISH_BOUNDARY_INVALID")

    sources = research.get("sources")
    claims = research.get("claims")
    if not isinstance(sources, list) or len(sources) < 2:
        raise Blocked("RESEARCH_MINIMUM_TWO_SOURCES_REQUIRED")
    if not isinstance(claims, list) or len(claims) < 3:
        raise Blocked("RESEARCH_MINIMUM_THREE_CLAIMS_REQUIRED")

    urls = set()
    for src in sources:
        if not isinstance(src, dict):
            raise Blocked("RESEARCH_SOURCE_INVALID")
        title = str(src.get("title") or "").strip()
        url = str(src.get("url") or "").strip()
        if not title or not url.startswith(("https://", "http://")):
            raise Blocked("RESEARCH_SOURCE_INVALID")
        urls.add(url)
    if len(urls) < 2:
        raise Blocked("RESEARCH_DISTINCT_SOURCES_REQUIRED")

    by = {}
    for claim in claims:
        if not isinstance(claim, dict):
            raise Blocked("RESEARCH_CLAIM_INVALID")
        fid = str(claim.get("fact_id") or "").strip()
        evidence = str(claim.get("evidence_text") or "")
        url = str(claim.get("source_url") or "")
        statement = str(claim.get("statement") or "").strip()
        if not fid or fid in by:
            raise Blocked("RESEARCH_FACT_ID_INVALID:" + fid)
        if not evidence.strip() or _sha_text(evidence) != claim.get("evidence_text_sha256"):
            raise Blocked("RESEARCH_EVIDENCE_HASH_INVALID:" + fid)
        if url not in urls:
            raise Blocked("RESEARCH_SOURCE_BINDING_INVALID:" + fid)
        if not statement:
            raise Blocked("RESEARCH_STATEMENT_EMPTY:" + fid)
        by[fid] = claim
    return by


def validate_article(article: dict, item: dict, portal_key: str, profile: dict, claims: dict[str, dict]) -> dict:
    if article.get("contract") != ARTICLE_CONTRACT:
        raise Blocked("ARTICLE_CONTRACT_INVALID")
    if article.get("portal_key") != portal_key:
        raise Blocked("ARTICLE_PORTAL_MISMATCH")
    if article.get("publish_allowed") is not False:
        raise Blocked("ARTICLE_PUBLISH_BOUNDARY_INVALID")

    allowed_categories = profile.get("allowed_categories")
    if not isinstance(allowed_categories, list) or not allowed_categories:
        raise Blocked("PORTAL_ALLOWED_CATEGORIES_INVALID")
    if item["category"] not in allowed_categories:
        raise Blocked("CATEGORY_NOT_ALLOWED_FOR_PORTAL:" + item["category"])

    binding = article.get("planning_binding")
    if not isinstance(binding, dict) or set(binding) != set(FIVE_FIELDS):
        raise Blocked("ARTICLE_PLANNING_BINDING_INVALID")
    if any(binding.get(k) != item[k] for k in FIVE_FIELDS):
        raise Blocked("ARTICLE_PLANNING_BINDING_MISMATCH")

    body = str(article.get("html") or "")
    if not body.strip():
        raise Blocked("ARTICLE_HTML_EMPTY")
    low = _visible(body).casefold()

    forbidden = ((profile.get("portal_rules") or {}).get("forbidden_cross_portal_terms") or [])
    leaks = [term for term in forbidden if str(term).casefold() in low]
    if leaks:
        raise Blocked("CROSS_PORTAL_CONTENT_LEAK:" + ",".join(leaks))

    if re.search(r"(?is)<h1\b", body):
        raise Blocked("BODY_H1_FORBIDDEN")
    h2s = re.findall(r"(?is)<h2\b[^>]*>(.*?)</h2>", body)
    if not 3 <= len(h2s) <= 7:
        raise Blocked("H2_COUNT_OUT_OF_RANGE:" + str(len(h2s)))
    paragraphs = re.findall(r"(?is)<p\b[^>]*>(.*?)</p>", body)
    if len(paragraphs) < 7:
        raise Blocked("PARAGRAPH_COUNT_TOO_LOW:" + str(len(paragraphs)))

    wc = len(_words(body))
    if not 450 <= wc <= 1000:
        raise Blocked("WORD_COUNT_OUT_OF_RANGE:" + str(wc))

    first = _visible(paragraphs[0]) if paragraphs else ""
    first_sentence = re.split(r"(?<=[.!?])\s+", first)[0].strip()
    first_wc = len(_words(first_sentence))
    if not 8 <= first_wc <= 35:
        raise Blocked("INTRO_ORIENTATION_SENTENCE_INVALID:" + str(first_wc))

    target = item["target_keyword"].casefold()
    target_count = low.count(target)
    if target_count > 8:
        raise Blocked("TARGET_PHRASE_OVERUSED:" + str(target_count))

    used = []
    for raw in re.findall(r'data-fact-ids\s*=\s*["\']([^"\']+)["\']', body, re.I):
        used.extend(raw.split())
    used_set = set(used)
    if len(used_set) < 3:
        raise Blocked("ARTICLE_MINIMUM_THREE_FACTS_REQUIRED")
    unknown = sorted(used_set - set(claims))
    if unknown:
        raise Blocked("ARTICLE_UNKNOWN_FACT_IDS:" + ",".join(unknown))

    conclusion = re.search(r'(?is)<section\b[^>]*data-block=["\']conclusion["\'][^>]*>(.*?)</section>', body)
    if not conclusion:
        raise Blocked("CONCLUSION_REQUIRED")
    if len(_words(conclusion.group(1))) < 45:
        raise Blocked("CONCLUSION_TOO_SHORT")

    return {
        "word_count": wc,
        "h2_count": len(h2s),
        "paragraph_count": len(paragraphs),
        "fact_ids_used": sorted(used_set),
        "target_phrase_count": target_count,
        "intro_first_sentence_words": first_wc,
    }


def produce(run_dir: str, profiles_dir: str, out_dir: str) -> dict:
    root = Path(run_dir)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    intake = _load(root / "INTAKE.json")
    research = _load(root / "RESEARCH.json")
    article = _load(root / "ARTICLE.json")

    receipt = route(intake, Path(profiles_dir))
    portal_key = receipt["portal_key"]
    item = receipt["article_identity"]
    profile = load_profile(Path(profiles_dir), portal_key)
    claims = validate_research(research, item, portal_key)
    metrics = validate_article(article, item, portal_key, profile, claims)

    final = {
        "contract": FINAL_CONTRACT,
        "status": "READY_FOR_OUTPUT",
        "portal_key": portal_key,
        "portal_name": profile["display_name"],
        "output_adapter": profile["output_adapter"],
        "job_identity_sha256": receipt["job_identity_sha256"],
        "title": item["title"],
        "target_keyword": item["target_keyword"],
        "category": item["category"],
        "article_type": item["article_type"],
        "plan_slot": item["plan_slot"],
        "body": article["html"],
        "research_source_count": len(research["sources"]),
        "research_claim_count": len(claims),
        "quality_metrics": metrics,
        "publish_allowed": False,
    }
    _save(out / "FINAL_ARTICLE.json", final)
    _save(out / "ROUTE_RECEIPT.json", receipt)
    print(json.dumps(final, ensure_ascii=False, indent=2))
    return final


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: production.py RUN_DIR PROFILES_DIR OUT_DIR")
    try:
        produce(sys.argv[1], sys.argv[2], sys.argv[3])
    except Blocked as exc:
        print(json.dumps({"contract": FINAL_CONTRACT, "status": "BLOCKED", "reason": str(exc), "publish_allowed": False}, ensure_ascii=False, indent=2))
        raise SystemExit(2)


if __name__ == "__main__":
    main()
