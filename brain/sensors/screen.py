import base64
import hashlib
import os
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image


MAX_SCREENSHOT_SIZE = (1280, 720)


class ScreenCaptureError(RuntimeError):
    pass


def capture_screen_base64(display: str | None = None) -> dict:
    display_value = display or os.getenv('DISPLAY', ':1')
    env = os.environ.copy()
    env['DISPLAY'] = display_value

    with tempfile.TemporaryDirectory() as temp_dir:
        screenshot_path = Path(temp_dir) / 'screen.png'
        result = subprocess.run(
            ['scrot', str(screenshot_path)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0 or not screenshot_path.exists():
            raise ScreenCaptureError(result.stderr.strip() or 'Falha ao capturar screenshot com scrot.')

        with Image.open(screenshot_path) as image:
            image = image.convert('RGB')
            original_width, original_height = image.size
            image.thumbnail(MAX_SCREENSHOT_SIZE)
            width, height = image.size
            buffer = BytesIO()
            image.save(buffer, format='PNG', optimize=True)

        image_bytes = buffer.getvalue()
        image_b64 = base64.b64encode(image_bytes).decode('utf-8')
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        return {
            'base64': image_b64,
            'hash': image_hash,
            'display': display_value,
            'width': width,
            'height': height,
            'original_width': original_width,
            'original_height': original_height,
        }
