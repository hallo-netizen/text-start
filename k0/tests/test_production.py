import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from k0.engine.production import Blocked, produce

ROOT = Path(__file__).resolve().parents[1]
PROFILES = ROOT / "portals"


def claim(fid, url, text, statement):
    return {
        "fact_id": fid,
        "source_url": url,
        "evidence_text": text,
        "evidence_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "statement": statement,
    }


def fixture(portal="hobbydepot"):
    slot = "a" * 64
    item = {
        "article_type": "FAQ",
        "category": "test",
        "plan_slot": slot,
        "target_keyword": "Beispiel erklären",
        "title": "Wie lässt sich ein Beispiel erklären?",
    }
    intake = {"contract": "K0_CENTRAL_INTAKE_V1", "portal_key": portal, "item": item, "publish_allowed": False}
    sources = [
        {"title": "Quelle A", "url": "https://example.org/a"},
        {"title": "Quelle B", "url": "https://example.org/b"},
    ]
    claims = [
        claim("F1", sources[0]["url"], "Beleg A erklärt den ersten Zusammenhang.", "Erster Zusammenhang."),
        claim("F2", sources[1]["url"], "Beleg B erklärt den zweiten Zusammenhang.", "Zweiter Zusammenhang."),
        claim("F3", sources[0]["url"], "Beleg C erklärt den dritten Zusammenhang.", "Dritter Zusammenhang."),
    ]
    research = {"contract": "K0_RESEARCH_V1", "portal_key": portal, "plan_slot": slot, "sources": sources, "claims": claims, "publish_allowed": False}
    para = " ".join(["Dieser Abschnitt erklärt den praktischen Zusammenhang verständlich und ordnet die wichtigsten Punkte für Leser nachvollziehbar ein."] * 5)
    html = (
        '<article><section data-block="intro"><p data-fact-ids="F1">Ein gutes Beispiel macht einen abstrakten Zusammenhang schnell verständlich und schafft eine klare Orientierung für den folgenden Text. '
        + para + '</p></section>'
        + '<section data-block="details"><h2>Der erste Zusammenhang</h2><p data-fact-ids="F1">' + para + '</p><p data-fact-ids="F1">' + para + '</p></section>'
        + '<section data-block="practice"><h2>Der zweite Zusammenhang</h2><p data-fact-ids="F2">' + para + '</p><p data-fact-ids="F2">' + para + '</p></section>'
        + '<section data-block="context"><h2>Der dritte Zusammenhang</h2><p data-fact-ids="F3">' + para + '</p><p data-fact-ids="F3">' + para + '</p></section>'
        + '<section data-block="conclusion"><h2>Fazit</h2><p data-fact-ids="F1 F2 F3">' + para + '</p></section></article>'
    )
    article = {"contract": "K0_ARTICLE_V1", "portal_key": portal, "planning_binding": item, "html": html, "publish_allowed": False}
    return intake, research, article


class ProductionTests(unittest.TestCase):
    def _run(self, portal="hobbydepot", mutate=None):
        intake, research, article = fixture(portal)
        if mutate:
            mutate(intake, research, article)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run = root / "run"; out = root / "out"; run.mkdir()
            for name, obj in (("INTAKE.json", intake), ("RESEARCH.json", research), ("ARTICLE.json", article)):
                (run / name).write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
            return produce(str(run), str(PROFILES), str(out))

    def test_real_pipeline_shape_passes_same_engine_hobby(self):
        self.assertEqual(self._run("hobbydepot")["status"], "READY_FOR_OUTPUT")

    def test_real_pipeline_shape_passes_same_engine_gaumen(self):
        self.assertEqual(self._run("gaumenatelier")["portal_key"], "gaumenatelier")

    def test_cross_portal_leak_blocks(self):
        def mutate(i, r, a):
            a["html"] = a["html"].replace("Fazit", "Fazit Pferdeatelier", 1)
        with self.assertRaisesRegex(Blocked, "CROSS_PORTAL_CONTENT_LEAK"):
            self._run("gaumenatelier", mutate)

    def test_bad_evidence_hash_blocks(self):
        def mutate(i, r, a):
            r["claims"][0]["evidence_text_sha256"] = "0" * 64
        with self.assertRaisesRegex(Blocked, "RESEARCH_EVIDENCE_HASH_INVALID"):
            self._run("hobbydepot", mutate)

    def test_wrong_portal_binding_blocks(self):
        def mutate(i, r, a):
            a["portal_key"] = "gaumenatelier"
        with self.assertRaisesRegex(Blocked, "ARTICLE_PORTAL_MISMATCH"):
            self._run("hobbydepot", mutate)

    def test_publish_true_blocks(self):
        def mutate(i, r, a):
            a["publish_allowed"] = True
        with self.assertRaisesRegex(Blocked, "ARTICLE_PUBLISH_BOUNDARY_INVALID"):
            self._run("hobbydepot", mutate)


if __name__ == "__main__":
    unittest.main()
