import csv
import io
from schemas.gherkin import Feature, Scenario, Step

def _render_steps(steps: list[Step], indent: str) -> str:
    return "\n".join(f"{indent}{s.keyword.value} {s.text}" for s in steps)

def feature_to_gherkin(feature: Feature) -> str:
    lines = []
    if feature.tags:
        lines.append(" ".join(f"@{t}" for t in feature.tags))
    lines.append(f"Feature: {feature.name}")
    if feature.description:
        for line in feature.description.splitlines():
            lines.append(f"  {line}")
    lines.append("")

    if feature.background:
        lines.append("  Background:")
        lines.append(_render_steps(feature.background, "    "))
        lines.append("")

    for sc in feature.scenarios:
        if sc.tags:
            lines.append("  "+" ".join(f"@{t}" for t in sc.tags))
        kind = "Scenario Outline" if sc.is_outline else "Scenario"
        lines.append(f"  {kind}: {sc.name}")
        lines.append(_render_steps(sc.steps, "    "))
        if sc.is_outline and sc.examples:
            lines.append("")
            lines.append("    Examples:")
            header = " | ".join(sc.examples.headers)
            lines.append(f"      | {header} |")
            for row in sc.examples.rows:
                lines.append(f"      | {' | '.join(row)} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"

def feature_to_csv(feature: Feature) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)

    writer.writerow(["Test ID", "Title", "Tags", "Type", "Steps", "Expected Result"])
    for i, sc in enumerate(feature.scenarios, start=1):
        actions = [s for s in sc.steps if s.keyword.value != "Then"]
        expected = [s for s in sc.steps if s.keyword.value == "Then"]
        steps_text = "\n".join(f"{s.keyword.value} {s.text}" for s in actions)
        expected_text = "\n".join(s.text for s in expected)
        test_type = next((t for t in sc.tags if t in {"functional", "negative", "edge", "regression"}), "functional")
        writer.writerow([f"TC-{i:03d}", sc.name, " ".join(sc.tags), test_type, steps_text, expected_text])
    
    return buf.getvalue()