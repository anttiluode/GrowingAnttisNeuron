from pathlib import Path


def test_pages_shell_exposes_developmental_controls_and_authority_note() -> None:
    html = Path("index.html").read_text(encoding="utf-8")

    assert 'id="arm"' in html
    assert 'value="guided"' in html
    assert 'value="shuffled_labels"' in html
    assert 'value="random_walk"' in html
    assert 'id="seed"' in html
    assert 'id="reset"' in html
    assert 'id="pause"' in html
    assert 'id="step"' in html
    assert 'id="development-canvas"' in html
    assert 'id="matrix-canvas"' in html
    assert "Python receipts are authoritative" in html
    assert 'href="site.css"' in html
    assert 'src="site.js"' in html


def test_pages_reports_frozen_v1_physical_bridge_without_browser_solver() -> None:
    html = Path("index.html").read_text(encoding="utf-8")
    script = Path("site.js").read_text(encoding="utf-8")

    assert "v1 physical bridge" in html.lower()
    assert "Python receipt" in html
    assert "purification" in html.lower()
    assert "identical passive cable" in html.lower()
    assert "physical.py" not in script
    assert "purification_time" not in script


def test_pages_assets_are_plain_static_files() -> None:
    script = Path("site.js").read_text(encoding="utf-8")
    css = Path("site.css").read_text(encoding="utf-8")

    assert "requestAnimationFrame" in script
    assert "guided" in script
    assert "shuffled_labels" in script
    assert "random_walk" in script
    assert "canvas" in css.lower()
