import argparse
import sys

from . import messages


def parse_args():
    parser = argparse.ArgumentParser(description="Glow your workflow")
    parser.add_argument("action")
    parser.add_argument("entity")
    parser.add_argument("key", nargs="*", default=None)
    return parser.parse_args()


def get_method_names(klass):
    return [
        func
        for func in dir(klass)
        if callable(getattr(klass, func)) and not func.startswith("_")
    ]


def ask(
    question,
    options=[
        "y",
    ],
    exit_tty=True,
):
    answer = messages.question(question)
    if answer.lower() not in options:
        messages.warning("Quitting...")

        if exit_tty:
            sys.exit(1)
