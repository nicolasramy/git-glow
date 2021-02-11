import json

from requests import Session

from . import messages


GITHUB_API_URL = "https://api.github.com"


def branch_exists(github_token, repository_name, branch_name):
    session = Session()

    headers = {
        "Authorization": "token {}".format(github_token),
        "Content-Type": "application/json",
    }

    response = session.get(
        "{}/repos/{}/branches/{}".format(
            GITHUB_API_URL,
            repository_name,
            branch_name,
        ),
        headers=headers,
    )

    if response.status_code != 200:
        return False

    try:
        commit_ref = response.json()["commit"]["sha"]

    except Exception as exc:
        messages.critical(exc)
        messages.critical(
            "{} branch was not found on remote repository.".format(branch_name)
        )
        return False

    return commit_ref


def create_branch(github_token, repository_name, commit_ref, commit_sha):
    session = Session()
    headers = {
        "Authorization": "token {}".format(github_token),
        "Content-Type": "application/json",
    }
    payload = {
        "ref": commit_ref,
        "sha": commit_sha,
    }
    response = session.post(
        "{}/repos/{}/git/refs".format(
            GITHUB_API_URL,
            repository_name,
        ),
        headers=headers,
        data=json.dumps(payload),
    )
    return response.status_code


def create_pull_request(
    github_token, repository_name, source_branch, dest_branch, title, body
):
    session = Session()

    headers = {
        "Authorization": "token {}".format(github_token),
        "Content-Type": "application/json",
    }
    payload = {
        "title": title,
        "body": body,
        "head": source_branch,
        "base": dest_branch,
    }

    response = session.post(
        "{}/repos/{}/pulls".format(GITHUB_API_URL, repository_name),
        headers=headers,
        data=json.dumps(payload),
    )

    if response.status_code == 201:
        return response.status_code, response.json().get("html_url")

    else:
        return response.status_code, [
            _.get("message") for _ in response.json().get("errors")
        ]
