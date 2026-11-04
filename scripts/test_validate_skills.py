"""Tests for validate_skills.py: python3 -m unittest discover -s scripts"""

import pathlib
import tempfile
import unittest

import validate_skills as v


def skill(tags_line: str):
    """A skill directory whose SKILL.md carries the given metadata.tags line (or none)."""
    tmp = pathlib.Path(tempfile.mkdtemp()) / "my-skill"
    tmp.mkdir()
    metadata = f"metadata:\n  version: \"1.0.0\"\n{tags_line}" if tags_line else "metadata:\n  version: \"1.0.0\"\n"
    (tmp / "SKILL.md").write_text(f"---\nname: my-skill\ndescription: Use when testing.\n{metadata}---\n\nBody.\n")
    return tmp


class TagTest(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(v.check_tags("kubernetes, incident-response, k8s2"), [])

    def test_missing_or_empty_is_valid(self):
        self.assertEqual(v.check_skill(skill("")), [])
        self.assertEqual(v.check_skill(skill('  tags: ""\n')), [])

    def test_format(self):
        for bad in ("Kubernetes", "incident_response", "-ci", "ci-", "ci--cd", "a b"):
            with self.subTest(bad=bad):
                self.assertTrue(any("hyphen-separated" in p for p in v.check_tags(bad)))

    def test_length(self):
        self.assertEqual(v.check_tags("a" * 63), [])
        self.assertTrue(any("limit is 63" in p for p in v.check_tags("a" * 64)))

    def test_duplicates(self):
        self.assertTrue(any("duplicate" in p for p in v.check_tags("ci, triage, ci")))

    def test_count(self):
        self.assertEqual(v.check_tags(", ".join(f"t{i}" for i in range(50))), [])
        self.assertTrue(any("limit is 50" in p for p in v.check_tags(", ".join(f"t{i}" for i in range(51)))))

    def test_skill_reports_tags(self):
        problems = v.check_skill(skill('  tags: "ok, Not-OK"\n'))
        self.assertEqual(len(problems), 1)
        self.assertIn("metadata.tags", problems[0])


if __name__ == "__main__":
    unittest.main()
