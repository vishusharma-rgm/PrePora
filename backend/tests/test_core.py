import os
import tempfile
import unittest
import atexit
from pathlib import Path
from uuid import uuid4


TEST_DB = Path(tempfile.gettempdir()) / f"prepora-test-{uuid4().hex}.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["APP_ENV"] = "test"
atexit.register(lambda: TEST_DB.unlink(missing_ok=True))

from backend.app import db  # noqa: E402
from backend.app.main import SESSION_QUESTIONS, TutorPayload, content_chapters, content_questions, tutor_response  # noqa: E402


class PrePoraCoreTests(unittest.TestCase):
    def test_complete_catalog_and_tutor_context(self):
        catalog = content_chapters("Mixed", "All")
        self.assertEqual(catalog["count"], 94)
        question_catalog = content_questions("Mixed", "Mixed", "Mixed", 500)
        self.assertGreaterEqual(question_catalog["count"], 564)
        reply = tutor_response(TutorPayload(prompt="Explain current electricity", subject="Physics", chapter="Current Electricity"), {})
        self.assertIn("V = IR", reply["reply"])

    def test_attempt_creates_review_work(self):
        user = db.create_user(f"test-{uuid4().hex[:8]}@example.com", "Test Student", "strongpass")
        session = db.create_session(user["id"], {"subject": "Mixed"}, SESSION_QUESTIONS[:2], 20)
        db.save_session_answer(user["id"], session["id"], 0, 0, True)
        db.save_session_answer(user["id"], session["id"], 1, 0, False)
        result = db.submit_session(user["id"], session["id"])
        self.assertEqual(result["status"], "submitted")
        self.assertEqual(result["correct"], 1)
        item = db.create_study_item(user["id"], {"kind": "queue", "subject": "Physics", "chapter": "Current Electricity"})
        self.assertEqual(db.list_study_items(user["id"])[0]["id"], item["id"])


if __name__ == "__main__":
    try:
        unittest.main()
    finally:
        TEST_DB.unlink(missing_ok=True)
