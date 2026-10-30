#!/usr/bin/env python
import os
import sys


# An empty value (as in .env.example) falls back to local.
def main() -> None:
    os.environ["DJANGO_SETTINGS_MODULE"] = (
        os.environ.get("DJANGO_SETTINGS_MODULE") or "config.settings.local"
    )
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
