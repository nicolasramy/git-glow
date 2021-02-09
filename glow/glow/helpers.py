import sys

from . import messages


def parse_args():
    parser = argparse.ArgumentParser(
            description="Glow your workflow"
        )
        parser.add_argument("action")
        parser.add_argument("entity")
        parser.add_argument("key", nargs="*", default=None)

        args = parser.parse_args()
        
    return args