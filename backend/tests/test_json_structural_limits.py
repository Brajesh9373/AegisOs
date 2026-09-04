"""Resource ceilings for JSON structural extraction."""

from legacy_ecms.pipeline.structural.json_parser import JsonStructuralExtractor


def test_json_artifact_count_is_bounded() -> None:
    content = (
        '{"items": [' + ",".join(f'{{"key_{index}": {index}}}' for index in range(1_000)) + "]}"
    )

    result = JsonStructuralExtractor(
        max_artifacts=25,
        max_depth=10,
        max_array_items=1_000,
    ).extract(content)

    assert not result.errors
    assert len(result.artifacts) == 25


def test_json_depth_and_array_width_are_bounded() -> None:
    result = JsonStructuralExtractor(
        max_artifacts=100,
        max_depth=3,
        max_array_items=2,
    ).extract('{"items":[{"a":{"deep":1}},{"b":2},{"c":3}]}')

    names = [artifact.name for artifact in result.artifacts]
    assert "$.items" in names
    assert "$.items[0].a" in names
    assert "$.items[0].a.deep" not in names
    assert all("[2]" not in name for name in names)
