#!/usr/bin/env python
"""Small compatibility CLI for the FastAPI backend."""

import argparse
import getpass
import sys

import uvicorn

from app import models  # noqa: F401
from app.core.database import Base, SessionLocal, engine
from app.core.security import make_password


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables are ready.")


def create_admin(args: argparse.Namespace) -> None:
    username = args.username or input("Username: ").strip()
    email = args.email or input("Email: ").strip()
    password = args.password or getpass.getpass("Password: ")
    if not username or not email or not password:
        raise SystemExit("username, email and password are required")

    with SessionLocal() as db:
        existing = db.query(models.User).filter(models.User.username == username).first()
        if existing:
            existing.email = email
            existing.password = make_password(password)
            existing.role = "admin"
            existing.is_staff = True
            existing.is_superuser = True
            existing.is_active = True
            existing.is_deleted = False
            print(f"Updated admin user: {username}")
        else:
            db.add(
                models.User(
                    username=username,
                    email=email,
                    password=make_password(password),
                    role="admin",
                    is_staff=True,
                    is_superuser=True,
                    is_active=True,
                )
            )
            print(f"Created admin user: {username}")
        db.commit()


def runserver(args: argparse.Namespace) -> None:
    host = "127.0.0.1"
    port = 8000
    if args.addrport:
        raw = args.addrport
        if ":" in raw:
            host, raw_port = raw.rsplit(":", 1)
            port = int(raw_port)
        else:
            port = int(raw)
    uvicorn.run("app.main:app", host=host, port=port, reload=args.reload,workers=2)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="FastAPI backend utility")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init-db", help="Create missing database tables")

    run = subparsers.add_parser("runserver", help="Run the FastAPI development server")
    run.add_argument("addrport", nargs="?", default="8000")
    run.add_argument("--reload", action="store_true", default=True)

    admin = subparsers.add_parser("create-admin", help="Create or update an admin user")
    admin.add_argument("--username")
    admin.add_argument("--email")
    admin.add_argument("--password")
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "init-db":
        init_db()
    elif args.command == "create-admin":
        init_db()
        create_admin(args)
    elif args.command == "runserver":
        runserver(args)


if __name__ == "__main__":
    main(sys.argv[1:])
