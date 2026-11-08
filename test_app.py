"""UI regression checks: no network is used by this suite."""
import io
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).with_name("app.py"))


class AppTests(unittest.TestCase):
    def setUp(self):
        self.api = patch("openai.OpenAI")
        self.client = self.api.start()
        self.addCleanup(self.api.stop)
        self.at = AppTest.from_file(APP, default_timeout=15).run()
        self.assertFalse(self.at.exception)

    def test_route_plan_changes_with_meal_time_without_api(self):
        from datetime import time
        self.at.time_input(key="tab1_time").set_value(time(12, 0)).run()
        self.at.button(key="tab1_btn").click().run()
        lunch = [x.value for x in self.at.success]
        self.assertEqual(len(lunch), 3)
        self.at.time_input(key="tab1_time").set_value(time(16, 0)).run()
        self.at.button(key="tab1_btn").click().run()
        self.assertNotEqual(lunch, [x.value for x in self.at.success])
        self.assertFalse(self.at.exception)
        self.client.assert_not_called()

    def test_manual_zero_and_positive_counts_work_without_cloud(self):
        for count, expected in [(0, "0.0 min"), (12, "9.6 min")]:
            self.at.number_input(key="tab2_manual").set_value(count).run()
            self.at.button(key="tab2_btn").click().run()
            self.assertEqual(self.at.metric[0].value, f"{count} people")
            self.assertEqual(self.at.metric[1].value, expected)
            self.assertFalse(self.at.exception)
        self.client.assert_not_called()

    def test_synthetic_demo_is_photo_free_and_explicit(self):
        self.at.radio(key="tab2_mode").set_value("Synthetic demo").run()
        self.assertTrue(any("16 synthetic" in warning.value for warning in self.at.warning))
        self.at.button(key="tab2_btn").click().run()
        self.assertEqual(self.at.metric[0].value, "16 people")
        self.client.assert_not_called()

    def test_photo_requires_consent_and_invalid_upload_shows_controlled_error(self):
        self.at.radio(key="tab2_mode").set_value("Photo estimate (cloud)").run()
        self.assertTrue(self.at.button(key="tab2_btn").disabled)
        self.at.file_uploader(key="tab2_uploader").upload("broken.png", b"not a photo").run()
        self.assertTrue(self.at.button(key="tab2_btn").disabled)
        self.at.checkbox(key="tab2_consent").check().run()
        self.at.button(key="tab2_btn").click().run()
        self.assertFalse(self.at.exception)
        self.assertTrue(self.at.error)
        self.assertFalse(self.at.metric)
        self.client.assert_not_called()

    def test_provider_failure_does_not_display_a_fake_headcount(self):
        image = io.BytesIO()
        Image.new("RGB", (20, 20)).save(image, "PNG")
        self.at.secrets["DASHSCOPE_API_KEY"] = "fake-test-key"
        self.client.side_effect = RuntimeError("private-provider-details")
        self.at.radio(key="tab2_mode").set_value("Photo estimate (cloud)").run()
        self.at.file_uploader(key="tab2_uploader").upload("test.png", image.getvalue()).run()
        self.at.checkbox(key="tab2_consent").check().run()
        self.at.button(key="tab2_btn").click().run()
        self.assertFalse(self.at.exception)
        self.assertFalse(self.at.metric)
        self.assertTrue(self.at.warning)
        self.assertNotIn("private-provider-details", " ".join(x.value for x in self.at.warning))


if __name__ == "__main__":
    unittest.main()
