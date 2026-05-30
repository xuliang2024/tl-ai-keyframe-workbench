from __future__ import annotations

from typing import Literal

ImageType = Literal["style", "character", "scene", "prop", "keyframe"]

NEGATIVE_CONSTRAINTS = (
    "no low quality, no blurry subject, no bad anatomy, no extra limbs, "
    "no distorted face, no unreadable clutter, no text, no watermark, no logo, "
    "no cartoon, no anime, no poster typography"
)

IMAGE_TYPE_REQUIREMENTS: dict[str, dict[str, str]] = {
    "style": {
        "title": "style reference image",
        "rules": (
            "Style reference image, no main character, no portrait, no recognizable hero, "
            "environment-focused composition, show worldbuilding, color palette, materials, lighting, "
            "architecture, weather, and 2-4 visual anchors. Use a wide establishing shot. "
            "Do not create a poster, character sheet, crowd portrait, battle scene, logo, or text layout."
        ),
        "composition": (
            "16:9 cinematic wide shot, environment occupies most of the image, tiny silhouettes only if needed for scale."
        ),
    },
    "character": {
        "title": "character asset reference image",
        "rules": (
            "Character asset reference image, single character only, pure color or low-texture background, "
            "clear face, clear costume details, clear invariant traits, neutral or slight expression. "
            "Do not use a complex environment, action scene, extra characters, text, logo, or poster layout."
        ),
        "composition": (
            "Half body or three-quarter body, eye-level camera, character occupies 55%-75% of the frame, "
            "background should be plain deep gray, cool blue-gray, or low-saturation dark teal."
        ),
    },
    "scene": {
        "title": "environment design image",
        "rules": (
            "Environment design image, no main character, clear spatial layout, show architecture, materials, lighting, "
            "scale, and 2-5 reusable scene landmarks. People may appear only as tiny scale-reference silhouettes."
        ),
        "composition": "16:9 wide or medium-wide shot, readable depth and structure, scene is the subject.",
    },
    "prop": {
        "title": "prop asset reference image",
        "rules": (
            "Prop asset reference image, single object only, pure color or low-texture background, clear silhouette, "
            "clear material, color, functional details, ports, seams, buttons, glow, and wear. "
            "Do not use complex background, table clutter, extra objects, text, logo, or exploded diagram."
        ),
        "composition": (
            "Three-quarter product view, object occupies 60%-80% of the frame, clean edges, "
            "background should be plain deep gray, cool blue-gray, or low-saturation dark teal."
        ),
    },
    "keyframe": {
        "title": "keyframe image",
        "rules": (
            "Keyframe image, one coherent cinematic story moment, show specific characters, action, emotion, setting, "
            "and camera language. Do not create a character sheet, pure mood board, poster, multiple panels, text, or logo."
        ),
        "composition": "16:9 film still, one clear narrative instant, readable subject, action, and environment.",
    },
}


def compose_image_prompt(
    *,
    image_type: str | None,
    prompt: str,
    project_style_prompt: str | None = None,
) -> str:
    if not image_type:
        return prompt

    normalized_type = image_type.strip().lower()
    requirement = IMAGE_TYPE_REQUIREMENTS.get(normalized_type)
    if not requirement:
        allowed = ", ".join(IMAGE_TYPE_REQUIREMENTS)
        raise ValueError(f"Unsupported image_type: {image_type}. Allowed values: {allowed}")

    parts = [
        f"[Image type]\n{requirement['title']}",
        f"[Fixed requirements]\n{requirement['rules']}",
        f"[Composition]\n{requirement['composition']}",
    ]
    if project_style_prompt and project_style_prompt.strip():
        parts.append(f"[Project style]\n{project_style_prompt.strip()}")
    parts.extend(
        [
            f"[User brief]\n{prompt.strip()}",
            f"[Negative constraints]\n{NEGATIVE_CONSTRAINTS}",
        ]
    )
    return "\n\n".join(parts)
