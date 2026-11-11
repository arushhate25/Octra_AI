from pathlib import Path

REQUIREMENTS = Path(__file__).resolve().parents[1] / "requirements.txt"


def test_requirements_pin_versions_and_include_dotenv():
    lines = [
        line.strip()
        for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    names = []
    for line in lines:
        name, sep, version = line.partition("==")
        assert sep == "==", f"{line} is not pinned with =="
        assert name and version and " " not in line
        names.append(name.lower())
    assert "python-dotenv" in names
