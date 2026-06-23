"""Muledance 2.0 Fast Reference-to-Video generation endpoint.

Lower latency / lower cost variant; capped at 720p.
Request must include at least one of `images` or `videos`. `audios`
cannot be used alone.

Path: /vendors/mulerouter/v1/muledance-2.0-fast/reference-to-video/generation.
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
    model_id="mule/muledance-2.0-fast-r2v",
    action="generation",
    provider="mule",
    model_name="muledance-2.0-fast-r2v",
    description=(
        "Fast variant of Muledance 2.0 Reference-to-Video (lower latency / lower cost). "
        "Up to 9 images, 3 videos, 3 audios as references. 480p or 720p, 4-15s."
    ),
    input_types=[InputType.IMAGE, InputType.VIDEO, InputType.TEXT],
    output_type=OutputType.VIDEO,
    api_path="/vendors/mulerouter/v1/muledance-2.0-fast/reference-to-video/generation",
    result_key="videos",
    available_on=["mulerouter", "mulerun"],
    parameters=[
        ModelParameter(
            name="prompt",
            type="string",
            description=(
                "Optional text prompt. Reference items by index: @Image1, @Image2, "
                "@Video1, @Audio1 etc. Wrap dialogue in double quotes."
            ),
            required=False,
        ),
        ModelParameter(
            name="images",
            type="array",
            description=(
                "Reference images (JSON array, 1-9 URLs or Base64 data URIs). "
                "jpeg/png/webp/bmp/tiff/gif/heic/heif. AR (0.4, 2.5), edge 300-6000 px, <= 30 MB."
            ),
            required=False,
        ),
        ModelParameter(
            name="videos",
            type="array",
            description=(
                "Reference videos (JSON array, 1-3 HTTPS URLs only; Base64 not supported). "
                "mp4/mov. Per-video [2,15]s, combined <= 15s. <= 50 MB. "
                "Fast variant: 480p-720p only."
            ),
            required=False,
        ),
        ModelParameter(
            name="audios",
            type="array",
            description=(
                "Reference audios (JSON array, 1-3 URLs or Base64 data URIs). "
                "wav/mp3. Per-audio [2,15]s, combined <= 15s. <= 15 MB. "
                "Cannot be supplied without at least one image or video."
            ),
            required=False,
        ),
        ModelParameter(
            name="resolution",
            type="string",
            description="Output video resolution (fast variant: no 1080p)",
            required=False,
            default="720p",
            enum=["480p", "720p"],
        ),
        ModelParameter(
            name="aspect_ratio",
            type="string",
            description="Aspect ratio; 'adaptive' uses prompt+references (video > image priority)",
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


class Muledance20FastR2VGeneration(BaseModelEndpoint):
    """Muledance 2.0 Fast Reference-to-Video generation endpoint."""

    @property
    def endpoint_info(self) -> ModelEndpoint:
        return ENDPOINT


def main() -> int:
    """CLI entry point."""
    return Muledance20FastR2VGeneration().run()


if __name__ == "__main__":
    raise SystemExit(main())
