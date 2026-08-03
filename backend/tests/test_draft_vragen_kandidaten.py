import importlib.util
from pathlib import Path

_pad = Path(__file__).resolve().parents[2] / "scripts" / "draft_vragen.py"
_spec = importlib.util.spec_from_file_location("draft_vragen", _pad)
draft_vragen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(draft_vragen)


def test_laad_kandidaten_merges_and_dedupes(tmp_path):
    yaml_pad = tmp_path / "k.yaml"
    yaml_pad.write_text(
        "- vraag: Wat is een AI-systeem?\n  sector: zorg\n"
        "- vraag: Wat is een AI-systeem?\n"          # dubbele → één keer
        "- vraag: Wanneer gelden de plichten?\n",
        encoding="utf-8",
    )
    kandidaten = draft_vragen.laad_kandidaten(str(yaml_pad), ["Wat is GPAI?"])
    vragen = [k["vraag"] for k in kandidaten]
    assert "Wat is een AI-systeem?" in vragen
    assert "Wat is GPAI?" in vragen                  # ingezonden meegevoegd
    assert len(vragen) == len(set(draft_vragen.slug(v) for v in vragen))  # uniek op slug
    # eerste (met sector) wint bij een dubbele
    z = next(k for k in kandidaten if k["vraag"] == "Wat is een AI-systeem?")
    assert z.get("sector") == "zorg"
