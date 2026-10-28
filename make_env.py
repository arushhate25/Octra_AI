import secrets
from pathlib import Path

env = Path(".env")
if env.exists():
    print(".env already exists. Delete it first if you want new keys.")
    raise SystemExit

names = ["SUPPORT_AGENT_KEY", "PAYMENTS_AGENT_KEY", "REVIEWER_KEY"]
env.write_text("\n".join(f"{n}={secrets.token_hex(16)}" for n in names) + "\n")

# Make sure git never uploads the keys.
gitignore = Path(".gitignore")
lines = gitignore.read_text().splitlines() if gitignore.exists() else []
if ".env" not in lines:
    with gitignore.open("a") as f:
        f.write("\n.env\n")

print("Created .env with three keys.")