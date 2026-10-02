import json
import unittest
from pathlib import Path

from k0.engine.router import Blocked, route

HERE = Path(__file__).resolve().parent
PROFILES = HERE / "fixtures" / "profiles"
SLOT = "a" * 64


def intake(portal_key="alpha", article_type="Beratung"):
    return {
        "contract": "K0_CENTRAL_INTAKE_V1",
        "portal_key": portal_key,
        "item": {
            "article_type": article_type,
            "category": "beispiel",
            "plan_slot": SLOT,
            "target_keyword": "Beispielthema",
            "title": "Beispielartikel",
        },
        "publish_allowed": False,
    }


class RouterTests(unittest.TestCase):
    def test_same_engine_routes_alpha(self):
        r = route(intake("alpha"), PROFILES)
        self.assertEqual(r["status"], "READY_FOR_K0_PRODUCTION")
        self.assertEqual(r["portal_key"], "alpha")
        self.assertFalse(r["publish_allowed"])

    def test_same_engine_routes_beta(self):
        r = route(intake("beta", "FAQ"), PROFILES)
        self.assertEqual(r["portal_key"], "beta")
        self.assertEqual(r["profile_display_name"], "Beta Testportal")

    def test_unknown_portal_blocks(self):
        with self.assertRaisesRegex(Blocked, "PORTAL_PROFILE_NOT_FOUND"):
            route(intake("unknown"), PROFILES)

    def test_inactive_portal_blocks(self):
        with self.assertRaisesRegex(Blocked, "PORTAL_PROFILE_INACTIVE"):
            route(intake("inactive"), PROFILES)

    def test_missing_portal_blocks(self):
        row = intake()
        row.pop("portal_key")
        with self.assertRaisesRegex(Blocked, "PORTAL_KEY_INVALID"):
            route(row, PROFILES)

    def test_extra_article_field_blocks(self):
        row = intake()
        row["item"]["portal"] = "alpha"
        with self.assertRaisesRegex(Blocked, "ARTICLE_IDENTITY_NOT_EXACT_FIVE_FIELDS"):
            route(row, PROFILES)

    def test_publish_true_blocks(self):
        row = intake()
        row["publish_allowed"] = True
        with self.assertRaisesRegex(Blocked, "PUBLISH_ALLOWED_MUST_BE_FALSE"):
            route(row, PROFILES)

    def test_disallowed_type_blocks(self):
        with self.assertRaisesRegex(Blocked, "ARTICLE_TYPE_NOT_ALLOWED_FOR_PORTAL"):
            route(intake("beta", "Vergleich"), PROFILES)


if __name__ == "__main__":
    unittest.main()
