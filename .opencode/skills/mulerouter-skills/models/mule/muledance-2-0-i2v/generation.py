"""Muledance 2.0 Image-to-Video generation endpoint.

Brand-wrapped ByteDance Doubao Seedance 2.0 served via MuleRouter at
/vendors/mulerouter/v1/muledance-2.0/image-to-video/generation.

Parameter contract follows docs/api/mule/muledance-2.0/image-to-video.
"""

import sys
from pathlib import Path

_file_dir = Path(__file__).parent
_models_dir = _file_dir.parent.parent
_root_dir = _models_dir.parent

if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from core import InputType, ModelEndpoint, ModelParameter, OutputType, register_endpoint
from models.base import BaseModelEndpoint

ENDPOINT = ModelEndpoint(
    model_id="mule/muledance-2.0-i2v",
    action="generation",
    provider="mule",
    model_name="muledance-2.0-i2v",
    description=(
        "Generate videos from a first-frame image (optional last-frame) using "
        "Muledance 2.0 (brand-wrapped ByteDance Doubao Seedance 2.0). "
        "480p/720p/1080p, 4-15s, synchronized audio."
    ),
    input_types=[InputType.IMAGE, InputType.TEXT],
    output_type=OutputType.VIDEO,
    api_path="/vendors/mulerouter/v1/muledance-2.0/image-to-video/generation",
    result_key="videos",
    available_on=["mulerouter", "mulerun"],
    parameters=[
        ModelParameter(
            name="image",
            type="string",
            description=(
                "First-frame image (URL or Base64 data URI). "
                "Format: jpeg/png/webp/bmp/tiff/gif/heic/heif. "
                "Aspect ratio (0.4, 2.5), edge 300-6000 px, <= 30 MB."
            ),
            required=True,
        ),
        ModelParameter(
            name="last_frame_image",
            type="string",
            description=(
                "Optional last-frame image (URL or Base64). When provided, the "
                "model interpolates between image (first) and last_frame_image. "
                "First-frame aspect ratio wins; last frame is center-cropped."
            ),
            required=False,
        ),
        ModelParameter(
            name="prompt",
            type="string",
            description=(
                "Optional text prompt describing the desired motion/scene. "
                "Wrap dialogue in double quotes for lip-sync."
            ),
            required=False,
        ),
        ModelParameter(
            name="resolution",
            type="string",
            description="Output video resolution",
            required=False,
            default="720p",
            enum=["480p", "720p", "1080p"],
        ),
        ModelParameter(
            name="aspect_ratio",
            type="string",
            description="Aspect ratio; 'adaptive' picks the closest to first-frame image",
            required=False,
            default="adaptive",
            enum=["16:9", "4:3", "1:1", "3:4", "9:16", "21:9", "adaptive"],
        ),
        ModelParameter(
            name="duration",
            type="integer",
            description="Video duration in whole seconds [4, 15], or -1 for model auto-pick",
            required=False,
            default=5,
        ),
        ModelParameter(
            name="generate_audio",
            type="boolean",
            description="Generate synchronized audio (mono output)",
            required=False,
            default=True,
        ),
        ModelParameter(
            name="seed",
            type="integer",
            description="Random seed in [-1, 4294967295]; -1/omit yields fresh seed each call",
            required=False,
        ),
    ],
)

register_endpoint(ENDPOINT)


class Muledance20I2VGeneration(BaseModelEndpoint):
    """Muledance 2.0 Image-to-Video generation endpoint."""

    @property
    def endpoint_info(self) -> ModelEndpoint:
        return ENDPOINT


def main() -> int:
    """CLI entry point."""
    return Muledance20I2VGeneration().run()


if __name__ == "__main__":
    raise SystemExit(main())
