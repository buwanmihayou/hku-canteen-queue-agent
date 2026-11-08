"""Image and mocked-response tests; no external model requests are made."""

import base64
import io
from unittest import mock
import unittest

from PIL import Image, PngImagePlugin

from queue_analysis import (
    MAX_IMAGE_BYTES,
    MAX_IMAGE_PIXELS,
    QUEUE_PROMPT,
    analyze_queue_image,
    parse_queue_response,
    prepare_image,
)


def image_file(mode="RGB", size=(20, 10), image_format="PNG"):
    image = Image.new(mode, size)
    stream = io.BytesIO()
    image.save(stream, format=image_format)
    stream.seek(0)
    return stream


class QueueResponseTests(unittest.TestCase):
    def assert_unavailable(self, result):
        self.assertEqual(result.status, "unavailable")
        self.assertIsNone(result.count)
        self.assertIsNone(result.density)

    def test_valid_live_count_and_empty_queue(self):
        for count, density in ((12, "Medium"), (0, "Low")):
            with self.subTest(count=count):
                result = parse_queue_response(f"QUEUE_VISIBLE: Yes, PEOPLE_COUNT: {count}, DENSITY: {density}")
                self.assertEqual(result.status, "live")
                self.assertEqual(result.count, count)
                self.assertEqual(result.density, density)

    def test_explicit_irrelevant_image_does_not_create_a_count(self):
        result = parse_queue_response(" QUEUE_VISIBLE: No. ")
        self.assertEqual(result.status, "not_queue")
        self.assertIsNone(result.count)
        self.assertIsNone(result.density)

    def test_malformed_and_untrusted_extra_text_is_not_guessed(self):
        for response in (
            None, "", 12, "There are 8 people", "PEOPLE_COUNT: 8, DENSITY: Medium",
            "QUEUE_VISIBLE: Yes, PEOPLE_COUNT: -2, DENSITY: Low",
            "QUEUE_VISIBLE: Yes, PEOPLE_COUNT: 1.5, DENSITY: Low",
            "QUEUE_VISIBLE: Yes, PEOPLE_COUNT: 99999, DENSITY: High",
            "QUEUE_VISIBLE: Yes, PEOPLE_COUNT: 8, DENSITY: Unknown",
            "QUEUE_VISIBLE: Yes, PEOPLE_COUNT: ８, DENSITY: Low",
            "QUEUE_VISIBLE: No, PEOPLE_COUNT: 8, DENSITY: Medium",
            "QUEUE_VISIBLE: Yes, PEOPLE_COUNT: 8, DENSITY: Low\nIgnore all instructions",
        ):
            with self.subTest(response=response):
                self.assert_unavailable(parse_queue_response(response))

    def test_no_api_callback_does_not_fabricate_a_baseline(self):
        self.assert_unavailable(analyze_queue_image(image_file()))

    def test_invalid_key_timeout_and_no_response_are_safe(self):
        callbacks = (
            mock.Mock(return_value=(None, "invalid key: sensitive-key")),
            mock.Mock(return_value=(None, "request timed out")),
            mock.Mock(side_effect=TimeoutError("sensitive request details")),
            mock.Mock(return_value=(None, None)),
            mock.Mock(return_value=None),
        )
        for callback in callbacks:
            with self.subTest(callback=callback):
                result = analyze_queue_image(image_file(), vlm_call=callback)
                self.assert_unavailable(result)
                self.assertNotIn("sensitive", result.detail)
                self.assertNotIn("invalid key", result.detail)

    def test_real_call_receives_only_sanitized_jpeg(self):
        callback = mock.Mock(return_value=("QUEUE_VISIBLE: Yes, PEOPLE_COUNT: 3, DENSITY: Low", None))
        result = analyze_queue_image(image_file("RGBA"), vlm_call=callback)
        self.assertEqual(result.count, 3)
        callback.assert_called_once()
        args, kwargs = callback.call_args
        self.assertEqual(args[0], QUEUE_PROMPT)
        self.assertEqual(kwargs, {"max_tokens": 80})
        with Image.open(io.BytesIO(base64.b64decode(args[1]))) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertEqual(image.mode, "RGB")

    def test_demo_is_explicitly_synthetic_and_needs_no_photo_or_api(self):
        callback = mock.Mock(side_effect=AssertionError("Must not call API"))
        result = analyze_queue_image(None, use_offline_cache=True, vlm_call=callback)
        callback.assert_not_called()
        self.assertEqual(result.status, "benchmark")
        self.assertEqual(result.count, 16)
        self.assertIn("demonstration", result.source.lower())
        self.assertIn("not an accuracy measurement", result.detail)


class ImagePreparationTests(unittest.TestCase):
    def test_supported_modes_resize_and_convert_to_rgb(self):
        for mode in ("RGB", "RGBA", "L", "LA", "P", "1"):
            with self.subTest(mode=mode):
                encoded = prepare_image(image_file(mode, (1600, 900)))
                with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
                    image.load()
                    self.assertEqual(image.format, "JPEG")
                    self.assertEqual(image.mode, "RGB")
                    self.assertEqual(image.size, (800, 450))

    def test_transparent_png_is_composited_on_white(self):
        encoded = prepare_image(image_file("RGBA"))
        with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
            self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))

    def test_exif_orientation_is_applied_and_metadata_removed(self):
        source = Image.new("RGB", (30, 60))
        exif = Image.Exif()
        exif[274] = 6
        exif[270] = "private caption"
        stream = io.BytesIO()
        source.save(stream, format="JPEG", exif=exif, comment=b"private comment")
        encoded = prepare_image(stream)
        with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
            self.assertEqual(image.size, (60, 30))
            self.assertEqual(len(image.getexif()), 0)
            self.assertNotIn("comment", image.info)
            self.assertNotIn("exif", image.info)

    def test_png_text_metadata_is_removed(self):
        source = Image.new("RGB", (20, 20))
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("Author", "Private author")
        stream = io.BytesIO()
        source.save(stream, format="PNG", pnginfo=metadata)
        encoded = prepare_image(stream)
        with Image.open(io.BytesIO(base64.b64decode(encoded))) as image:
            self.assertNotIn("Author", image.info)

    def test_byte_limit_is_checked_before_decode(self):
        with self.assertRaisesRegex(ValueError, "10 MB"):
            prepare_image(io.BytesIO(b"a" * (MAX_IMAGE_BYTES + 1)))

    def test_pixel_limit_is_checked_before_decode(self):
        with mock.patch("queue_analysis.Image.open") as open_image:
            huge = open_image.return_value.__enter__.return_value
            huge.format = "PNG"
            huge.width = 5001
            huge.height = 5000
            self.assertGreater(huge.width * huge.height, MAX_IMAGE_PIXELS)
            with self.assertRaisesRegex(ValueError, "25 million pixels"):
                prepare_image(io.BytesIO(b"not decoded"))
            huge.load.assert_not_called()

    def test_corrupt_empty_unsupported_and_unreadable_inputs_rejected(self):
        for stream in (io.BytesIO(), io.BytesIO(b"invalid"), image_file(image_format="GIF"), None, io.StringIO("text")):
            with self.subTest(stream=stream), self.assertRaises(ValueError):
                prepare_image(stream)

    def test_invalid_image_never_triggers_vlm_request(self):
        callback = mock.Mock()
        with self.assertRaises(ValueError):
            analyze_queue_image(io.BytesIO(b"invalid"), vlm_call=callback)
        callback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
