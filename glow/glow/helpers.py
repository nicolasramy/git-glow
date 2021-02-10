import argparse
import json

from requests import Session


def parse_args():
    parser = argparse.ArgumentParser(description="Glow your workflow")
    parser.add_argument("action")
    parser.add_argument("entity")
    parser.add_argument("key", nargs="*", default=None)

    args = parser.parse_args()

    return args


def create_pull_request(source_branch, dest_branch, title, body, github_token):
    session = Session()

    headers = {
        "Authorization": "token {}".format(github_token),
        "Content-Type": "application/json",
    }
    payload = {
        "": title,
        "body": body,
        "head": source_branch,
        "base": dest_branch,
    }

    response = session.post("", headers=headers, data=json.dumps(payload))
