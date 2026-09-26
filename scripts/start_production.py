"""Start Beacon's production API process from validated environment settings."""

import os

import uvicorn


def positive_integer(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as error:
        raise RuntimeError(f"{name} must be an integer") from error
    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def main() -> None:
    uvicorn.run(
        "main:app",
        host=os.getenv("API_BIND_HOST", "0.0.0.0"),
        port=positive_integer("API_PORT", 8000),
        workers=positive_integer("API_WORKERS", 1),
        proxy_headers=True,
        forwarded_allow_ips=os.getenv("FORWARDED_ALLOW_IPS", "127.0.0.1"),
        access_log=False,
    )


if __name__ == "__main__":
    main()
