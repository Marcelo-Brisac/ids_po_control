"""Muledance 2.0 Text-to-Video generation endpoint.

Brand-wrapped ByteDance Doubao Seedance 2.0 served via MuleRouter at
/vendors/mulerouter/v1/muledance-2.0/text-to-video/generation.

Parameter contract follows docs/api/mule/muledance-2.0/text-to-video.
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
    model_id="mule/muledance-2.0-t2v",
    action="generation",
    provider="mule",
    model_name="muledance-2.0-t2v",
    description=(
        "Generate videos from text prompts using Muledance 2.0 "
        "(brand-wrapped ByteDance Doubao Seedance 2.0). Native synchronized "
        "audio, 480p/720p/1080p, 4-15s, multilingual prompts."
    ),
    input_types=[InputType.TEXT],
    output_type=OutputType.VIDEO,
    api_path="/vendors/mulerouter/v1/muledance-2.0/text-to-video/generation",
    result_key="videos",
    available_on=["mulerouter", "mulerun"],
    parameters=[
        ModelParameter(
            name="prompt",
            type="string",
            description=(
                "Text prompt describing the desired video. "
                "Supports zh / en / ja / id / es / pt. Wrap dialogue in double "
                "quotes for lip-sync when generate_audio=true. "
                "Suggested length: <=500 zh chars or <=1000 en words."
            ),
            required=True,
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
            description="Aspect ratio; 'adaptive' lets the model pick from prompt content",
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
            description="Generate synchronized audio (dialogue/SFX/music). Output is mono.",
            required=False,
            default=True,
        ),
        ModelParameter(
            name="seed",
            type="integer",
            description="Random seed in [-1, 4294967295]; -1/omit yields fresh seed each call",
            required=False,
        ),
        ModelParameter(
            name="camera_fixed",
            type="boolean",
            description=(
                "Hint the model to keep camera static. "
                "Currently a no-op for Seedance 2.0 (accepted for forward compatibility)."
            ),
            required=False,
            default=False,
        ),
        ModelParameter(
            name="watermark",
            type="boolean",
            description='When true, an "AI generated" watermark is rendered bottom-right',
            required=False,
            default=False,
        ),
    ],
)

register_endpoint(ENDPOINT)


class Muledance20T2VGeneration(BaseModelEndpoint):
    """Muledance 2.0 Text-to-Video generation endpoint."""

    @property
    def endpoint_info(self) -> ModelEndpoint:
        return ENDPOINT


def main() -> int:
    """CLI entry point."""
    return Muledance20T2VGeneration().run()


if __name__ == "__main__":
    raise SystemExit(main())
