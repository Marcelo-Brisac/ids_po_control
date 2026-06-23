"""Muledance 2.0 Fast Text-to-Video generation endpoint.

Lower latency / lower cost variant; capped at 720p. Does NOT accept
`camera_fixed` or `watermark` (rejected by upstream payload validator).

Path: /vendors/mulerouter/v1/muledance-2.0-fast/text-to-video/generation.
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
    model_id="mule/muledance-2.0-fast-t2v",
    action="generation",
    provider="mule",
    model_name="muledance-2.0-fast-t2v",
    description=(
        "Fast variant of Muledance 2.0 Text-to-Video (lower latency / lower cost). "
        "480p or 720p only. Synchronized audio, 4-15s, multilingual prompts."
    ),
    input_types=[InputType.TEXT],
    output_type=OutputType.VIDEO,
    api_path="/vendors/mulerouter/v1/muledance-2.0-fast/text-to-video/generation",
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
            description="Output video resolution (fast variant: no 1080p)",
            required=False,
            default="720p",
            enum=["480p", "720p"],
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


class Muledance20FastT2VGeneration(BaseModelEndpoint):
    """Muledance 2.0 Fast Text-to-Video generation endpoint."""

    @property
    def endpoint_info(self) -> ModelEndpoint:
        return ENDPOINT


def main() -> int:
    """CLI entry point."""
    return Muledance20FastT2VGeneration().run()


if __name__ == "__main__":
    raise SystemExit(main())
