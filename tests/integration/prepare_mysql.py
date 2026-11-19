from pathlib import Path
import secrets


def main():
    project_root = Path(__file__).resolve().parents[2]
    venv = project_root / ".venv"

    if not venv.is_dir():
        raise SystemExit("Create the project's .venv first.")

    secret_dir = venv / "tv4_mysql"
    secret_dir.mkdir(parents=True, exist_ok=True)
    secret_dir.chmod(0o700)

    for name in ("app_password", "root_password"):
        path = secret_dir / name
        if not path.exists():
            path.write_text(secrets.token_urlsafe(32), encoding="utf-8")
        path.chmod(0o644)

    print("Local MySQL test credentials are ready.")


if __name__ == "__main__":
    main()