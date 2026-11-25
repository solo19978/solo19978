"""Check privacy boundaries, failed refreshes and graphic output."""
import collections
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

import build_profile as profile


class ProfileChecks(unittest.TestCase):
    def test_public_scope_and_date_window(self):
        repo = {"name": "tool", "full_name": "solo19978/tool", "private": False,
                "fork": False, "size": 1, "html_url": "https://github.com/solo19978/tool",
                "language": "Rust", "stargazers_count": 2}
        def response(path):
            if path.startswith("/users/"):
                return [repo, dict(repo, name="secret", private=True),
                        dict(repo, name="fork", fork=True), dict(repo, name="solo19978")]
            self.assertTrue(path.startswith("/repos/solo19978/tool/commits?"))
            today = profile.dt.datetime.now(profile.dt.timezone.utc).date()
            return [{"commit": {"author": {"date": str(day)+"T12:00:00Z"}}} for day in
                    [today, today-profile.dt.timedelta(days=83), today-profile.dt.timedelta(days=84)]]
        with patch.object(profile, "pages", side_effect=response):
            result = profile.collect()
        self.assertEqual(len(result["projects"]), 1)
        self.assertEqual(len(result["daily"]), 84)
        self.assertEqual(sum(day["commits"] for day in result["daily"]), 2)
        self.assertEqual(result["daily"][0]["commits"], 1)
        self.assertEqual(result["daily"][-1]["commits"], 1)

    def test_failed_collection_does_not_write(self):
        with patch.object(profile, "pages", side_effect=RuntimeError("API unavailable")), \
             patch.object(profile, "build") as build:
            with self.assertRaises(RuntimeError):
                profile.collect()
            build.assert_not_called()

    def test_pagination_collects_every_page(self):
        with patch.object(profile, "api", side_effect=[list(range(100)), [100]]) as api:
            self.assertEqual(profile.pages("/example?author=solo19978"), list(range(101)))
            self.assertIn("&per_page=100&page=2", api.call_args.args[0])

    def test_all_svgs_parse_and_empty_activity_renders(self):
        data = json.loads((profile.ROOT/"assets/public-activity.json").read_text())
        data["projects"] = []
        for day in data["daily"]:
            day["commits"] = 0
        with tempfile.TemporaryDirectory() as folder, patch.object(profile, "ROOT", Path(folder)):
            profile.build(data)
            paths = list((Path(folder)/"assets").glob("*.svg"))
            self.assertEqual(len(paths), 8)
            for path in paths:
                root = ET.parse(path).getroot()
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertNotIn("nan", path.read_text().lower())


if __name__ == "__main__":
    unittest.main()
