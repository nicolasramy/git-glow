import argparse
import errno
import json
import os
import sys

import colorama
from git import Repo
from git.exc import InvalidGitRepositoryError
import requests
import semver

from . import messages


class Glow(object):

    GITHUB_API_URL = "https://api.github.com"

    version = None

    repo = None
    config = None

    current_directory = None
    working_directory = None
    git_directory = None

    glow_config = None

    jira_project_key = None
    github_url = None
    github_repository_name = None
    github_token = None

    def _pull_branch(self, branch_name, create_branch=False):
        if create_branch:
            self.repo.git.pull("origin")
            self.repo.git.checkout("HEAD", b=branch_name)
        else:
            self.repo.git.checkout(branch_name)
            self.repo.git.pull("origin")

        messages.success('Branch "{}" pulled.'.format(branch_name))

    def _push_branch(self, branch_name):
        self.repo.git.push("origin", branch_name)

    def _pull_repository(self):
        """
        Pull develop and main branches and tags
        from origin and prune remote branches
        """
        ...

    @staticmethod
    def _push_repository():
        """Push develop and master branches and tags to origin"""
        ...

    @staticmethod
    def _generate_changelog(branch_from, branch_to):
        """Generate changelog between two branches"""
        ...

    def _branches(self):
        return [branch.name for branch in self.repo.branches]

    def _feature_exists(self, issue_id):
        issue_id = str(issue_id)
        feature_name = "feature/{}-{}".format(self.jira_project_key, issue_id)

        return feature_name in self._branches()

    def _create_config(self):
        self.jira_project_key = messages.question("Jira Project Key? ").upper()
        self.github_repository_name = messages.question(
            "Github Repository Name? [:owner/:name] "
        )
        self.github_token = messages.question("Github Token? ")

    def _init_repo(self):
        self.current_directory = os.getcwd()

        try:
            self.repo = Repo(
                self.current_directory, search_parent_directories=True
            )
            _ = self.repo.git.rev_parse("--show-toplevel")
            self.working_directory = self.repo.working_dir
            self.git_directory = self.repo.git_dir

        except InvalidGitRepositoryError:
            messages.critical("You are not in a git repository")
            sys.exit(errno.ENOENT)

    def _init_glow(self):
        with self.repo.config_reader() as config_reader:
            if config_reader.has_section("glow"):
                # fmt: off
                self.github_token = config_reader.get(
                    "glow", "github-token"
                )
                self.github_repository_name = config_reader.get(
                    "glow", "github-repository-name"
                )
                self.jira_project_key = config_reader.get(
                    "glow", "jira-project-key"
                )
                # fmt: on

            else:
                create_a_glow_file = messages.question(
                    "Create a glow config? [Y/n] "
                )

                if create_a_glow_file.lower() != "y":
                    messages.warning(
                        "Command can't be used without configuration"
                    )
                    sys.exit(errno.EPERM)

                else:
                    self._create_config()

                    with self.repo.config_writer() as config_writer:
                        # fmt: off
                        config_writer.add_section("glow")
                        config_writer.set(
                            "glow",
                            "github-token",
                            self.github_token,
                        )
                        config_writer.set(
                            "glow",
                            "github-repository-name",
                            self.github_repository_name,
                        )
                        config_writer.set(
                            "glow",
                            "jira-project-key",
                            self.jira_project_key,
                        )
                        # fmt: on

    def _init_version(self):
        tags = self.repo.tags

        if not tags:
            self.version = semver.VersionInfo.parse(self.version)

            messages.warning("No version found for this repository...")
            first_commit = self.repo.git.rev_list("--max-parents=0", "HEAD")
            messages.warning(
                "Generate first version «{}» on first commit".format(
                    self.version
                )
            )

            self.repo.create_tag(self.version, ref=first_commit)

            self.repo.git.push("origin", "--tags")
            messages.success(
                "Version {} pushed to remote repository".format(self.version)
            )

        else:
            messages.log("Latest version: ...")

    def __init__(self):
        """Initialize Github Flow CLI"""

        colorama.init(autoreset=True)

        self._init_repo()

        messages.info("Working Directory: {}".format(self.working_directory))
        messages.info("Git Directory: {}".format(self.git_directory))
        messages.info("Current Directory: {}".format(self.current_directory))

        self._init_glow()
        self._init_version()

    """ Feature methods """

    def start_feature(self, issue_id):
        try:
            issue_id = int(issue_id)

        except ValueError:
            messages.critical('IssueID "{}" is not valid.'.format(issue_id))
            sys.exit(1)

        except TypeError:
            messages.critical("IssueID is not set.")
            sys.exit(1)

        feature_name = "{}-{}".format(self.jira_project_key, issue_id)

        if self._feature_exists(issue_id):
            messages.error(
                "A feature locally exists for IssueID {}.".format(issue_id)
            )
            return False

        create_feature = messages.question(
            "Validate this feature name -> feature/{}? [y/n] ".format(
                feature_name
            )
        )
        if create_feature.lower() != "y":
            messages.warning("Quitting...")
            sys.exit(1)

        # Create remote and local branch
        session = requests.Session()

        headers = {
            "Authorization": "token {}".format(self.github_token),
            "Content-Type": "application/json",
        }

        response = session.get(
            "{}/repos/{}/branches/develop".format(
                self.GITHUB_API_URL,
                self.github_repository_name,
            ),
            headers=headers,
        )

        if response.status_code != 200:
            messages.critical(
                "An error occurred while retrieving develop branch."
            )
            return False

        try:
            commit_ref = response.json()["commit"]["sha"]

        except Exception as exc:
            messages.critical(exc)
            messages.critical(
                "develop branch was not found on remote repository."
            )
            return False

        payload = {
            "ref": "refs/heads/feature/{}".format(feature_name),
            "sha": commit_ref,
        }

        response = session.post(
            "{}/repos/{}/git/refs".format(
                self.GITHUB_API_URL,
                self.github_repository_name,
            ),
            headers=headers,
            data=json.dumps(payload),
        )

        if response.status_code == 201:
            messages.success(
                "New branch: feature/{} created".format(feature_name)
            )
            self._pull_branch(
                "feature/{}".format(feature_name), create_branch=True
            )
            messages.success(
                'Switched to a new branch "feature/{}".'.format(feature_name)
            )
            return True

        elif response.status_code == 422:
            messages.warning(
                "Feature branch feature/{} already exists.".format(feature_name)
            )
            self._pull_branch(
                "feature/{}".format(feature_name), create_branch=True
            )
            messages.success(
                'Switched to a new branch "feature/{}".'.format(feature_name)
            )
            return True

        else:
            messages.critical(
                "Feature branch feature/{} can not be created ({}: {}).".format(
                    feature_name,
                    response.status_code,
                    response.json()["message"],
                )
            )
            return False

    def review_feature(self, issue_id):
        try:
            issue_id = int(issue_id)

        except ValueError:
            messages.critical('IssueID "{}" is not valid.'.format(issue_id))
            sys.exit(1)

        except TypeError:
            messages.critical("IssueID is not set.")
            sys.exit(1)

        if not self._feature_exists(issue_id):
            messages.error(
                "There is no feature for IssueID {}.".format(issue_id)
            )
            sys.exit(1)

        feature_name = "feature/{}-{}".format(self.jira_project_key, issue_id)

        # Push feature branch to origin
        messages.log("Push feature branch «{}» to origin".format(feature_name))
        self._push_branch(feature_name)

        # Pull last modifications from develop
        messages.log("Pull last modifications from develop")
        self._pull_branch("develop")

        # Create a Pull Request for this feature branch into develop
        messages.log(
            "Create a Pull Request for this feature branch into develop"
        )
        session = requests.Session()

        headers = {
            "Authorization": "token {}".format(self.github_token),
            "Content-Type": "application/json",
        }

        title = feature_name.replace("feature/", "")
        payload = {
            "title": title,
            "body": title,
            "head": feature_name,
            "base": "develop",
        }

        response = session.post(
            "{}/repos/{}/pulls".format(
                self.GITHUB_API_URL,
                self.github_repository_name,
            ),
            headers=headers,
            data=json.dumps(payload),
        )

        if response.status_code == 201:
            messages.success(
                "New Pull Request created: {}".format(
                    response.json()["html_url"]
                )
            )
            return True

        else:
            messages.critical(response.json()["message"])
            for error in response.json()["errors"]:
                messages.error(error["message"])
            return False

    def cancel_feature(self, issue_id, description=None):
        messages.warning("Not implemented yet")

    """ Release methods """

    def start_release(self, is_master=False):
        """Open an application release"""
        self._pull_repository()

        # Change version
        if is_master:
            self.version["master"] += 1
        else:
            self.version["release"] += 1

        self.version["hotfix"] = 0

        create_release = messages.question(
            "Validate this release name -> release/{}? [y/n] ".format(
                self._str_version()
            )
        )
        if create_release.lower() != "y":
            messages.warning("Quitting...")
            sys.exit(errno.ENOMSG)

        # Create remote and local branch
        session = requests.Session()

        headers = {
            "Authorization": "token {}".format(
                self.glow_config.get("github", "token")
            ),
            "Content-Type": "application/json",
        }

        response = session.get(
            "{}/api/v3/repos/{}/git/refs/heads".format(
                self.glow_config.get("github", "url"),
                self.glow_config.get("github", "repository_name"),
            ),
            headers=headers,
        )

        if response.status_code != 200:
            messages.critical("An error occurred while retrieving refs.")
            return False

        commit_ref = None
        for item in response.json():
            if item["ref"] == "refs/heads/develop":
                commit_ref = item["object"]["sha"]
                break

        if not commit_ref:
            messages.critical(
                "develop branch was not found on remote repository."
            )
            return False

        payload = {
            "ref": "refs/heads/release/{}".format(self._str_version()),
            "sha": commit_ref,
        }

        response = session.post(
            "{}/api/v3/repos/{}/git/refs".format(
                self.glow_config.get("github", "url"),
                self.glow_config.get("github", "repository_name"),
            ),
            headers=headers,
            data=json.dumps(payload),
        )

        if response.status_code == 201:
            messages.success(
                "New branch: release/{} created".format(self._str_version())
            )

            if self._pull_branch(
                "release/{}".format(self._str_version()), create_branch=True
            ):
                messages.success(
                    'Switched to a new branch "release/{}".'.format(
                        self._str_version()
                    )
                )
                ...

            else:
                messages.critical(
                    "Unable to checkout to branch: release/{}".format(
                        self._str_version()
                    )
                )
                return False

        elif response.status_code == 422:
            messages.error(
                "Feature branch release/{} already exists.".format(
                    self._str_version()
                )
            )
            return False

        else:
            messages.critical(
                "Release branch release/{} can not be created ({}: {}).".format(
                    self._str_version(),
                    response.status_code,
                    response.json()["message"],
                )
            )
            return False

    def review_release(self, is_master=False):
        ...

    def finish_release(self, is_master=False):
        ...

    def cancel_release(self, is_master=False):
        messages.warning("Not implemented yet")

    """ Hotfix methods """

    def start_hotfix(self):
        """Open an application release"""
        self._pull_repository()

        # Change version
        self.version["hotfix"] += 1

        create_hotfix = messages.question(
            "Validate this hotfix name -> hotfix/{}? [y/n] ".format(
                self._str_version()
            )
        )
        if create_hotfix.lower() != "y":
            messages.warning("Quitting...")
            sys.exit(errno.ENOMSG)

        # Create remote and local branch
        session = requests.Session()

        headers = {
            "Authorization": "token {}".format(
                self.glow_config.get("github", "token")
            ),
            "Content-Type": "application/json",
        }

        response = session.get(
            "{}/api/v3/repos/{}/git/refs/heads".format(
                self.glow_config.get("github", "url"),
                self.glow_config.get("github", "repository_name"),
            ),
            headers=headers,
        )

        if response.status_code != 200:
            messages.critical("An error occurred while retrieving refs.")
            return False

        commit_ref = None
        for item in response.json():
            if item["ref"] == "refs/heads/master":
                commit_ref = item["object"]["sha"]
                break

        if not commit_ref:
            messages.critical(
                "master branch was not found on remote repository."
            )
            return False

        payload = {
            "ref": "refs/heads/hotfix/{}".format(self._str_version()),
            "sha": commit_ref,
        }

        response = session.post(
            "{}/api/v3/repos/{}/git/refs".format(
                self.glow_config.get("github", "url"),
                self.glow_config.get("github", "repository_name"),
            ),
            headers=headers,
            data=json.dumps(payload),
        )

        if response.status_code == 201:
            messages.success(
                "New branch: hotfix/{} created".format(self._str_version())
            )

            if self._pull_branch(
                "hotfix/{}".format(self._str_version()), create_branch=True
            ):
                messages.success(
                    'Switched to a new branch "hotfix/{}".'.format(
                        self._str_version()
                    )
                )
                return True

            else:
                messages.critical(
                    "Unable to checkout to branch: hotfix/{}".format(
                        self._str_version()
                    )
                )
                return False

        elif response.status_code == 422:
            messages.error(
                "Feature branch hotfix/{} already exists.".format(
                    self._str_version()
                )
            )
            return False

        else:
            messages.critical(
                "Release branch hotfix/{} can not be created ({}: {}).".format(
                    self._str_version(),
                    response.status_code,
                    response.json()["message"],
                )
            )
            return False

    def review_hotfix(self):
        ...

    def finish_hotfix(self):
        ...

    def cancel_hotfix(self):
        messages.warning("Not implemented yet")

    """Main"""

    def main(self):
        parser = argparse.ArgumentParser(
            description="Glow your workflow"
        )
        parser.add_argument("action")
        parser.add_argument("entity")
        parser.add_argument("key", nargs="*", default=None)

        args = parser.parse_args()

        methods_list = [
            func
            for func in dir(self)
            if callable(getattr(self, func)) and not func.startswith("_")
        ]
        method_name = "{}_{}".format(args.action, args.entity)

        if method_name not in methods_list:
            messages.error(
                "Unknown command «{} {}»".format(args.action, args.entity)
            )
            sys.exit(1)

        _func = getattr(self, method_name)
        _func(args.key)


if __name__ == "__main__":
    glow = Glow()
    glow.main()
