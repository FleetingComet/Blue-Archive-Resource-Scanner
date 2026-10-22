import numpy as np
import pytest

pytest.importorskip("win32gui")  # Desktop backend is Windows-only

from src.core.area import Region  # noqa: E402
from src.utils.device.desktop.window_manager import (  # noqa: E402
    crop_to_client,
    to_base_resolution,
)


class TestCropToClient:
    def test_crops_client_out_of_window_frame(self):
        # Windowed: 1px border left/right/bottom and a 31px title bar
        frame = Region(100, 50, 1838, 1065)
        client = Region(101, 81, 1836, 1033)
        image = np.zeros((frame.height, frame.width, 3), np.uint8)
        image[31, 1] = 255  # first client pixel
        image[31 + 1032, 1 + 1835] = 128  # last client pixel

        crop = crop_to_client(image, frame, client)

        assert crop.shape == (1033, 1836, 3)
        assert crop[0, 0, 0] == 255
        assert crop[-1, -1, 0] == 128

    def test_fullscreen_has_no_offset(self):
        region = Region(0, 0, 1920, 1080)
        image = np.zeros((1080, 1920, 3), np.uint8)
        assert crop_to_client(image, region, region).shape == (1080, 1920, 3)

    def test_rejects_capture_smaller_than_client(self):
        image = np.zeros((700, 1280, 3), np.uint8)
        with pytest.raises(RuntimeError):
            crop_to_client(image, Region(0, 0, 1280, 700), Region(0, 0, 1280, 720))

    def test_rejects_window_that_moved_during_capture(self):
        # Client read after a move sits left of the frame read before it
        image = np.zeros((767, 1284, 3), np.uint8)
        with pytest.raises(RuntimeError):
            crop_to_client(image, Region(210, 150, 1284, 767), Region(209, 195, 1280, 720))

    def test_rejects_capture_not_matching_frame_size(self):
        image = np.zeros((787, 1284, 3), np.uint8)  # frame grew during capture
        with pytest.raises(RuntimeError):
            crop_to_client(image, Region(0, 0, 1284, 767), Region(2, 45, 1280, 720))


class TestToBaseResolution:
    @pytest.mark.parametrize("size", [(1836, 1033), (1920, 1080), (960, 540)])
    def test_scales_to_1280x720(self, size):
        w, h = size
        image = np.zeros((h, w, 3), np.uint8)
        image[h // 2 :, w // 2 :] = 255  # bottom-right quadrant

        out = to_base_resolution(image)

        assert out.shape == (720, 1280, 3)
        assert out[100, 100, 0] == 0
        assert out[620, 1180, 0] == 255

    def test_keeps_1280x720_untouched(self):
        image = np.zeros((720, 1280, 3), np.uint8)
        assert to_base_resolution(image) is image
