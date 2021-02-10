import errno
import json
import os
import sys

import colorama
from git import Repo
from git.exc import InvalidGitRepositoryError
import requests
import semver

from . import helpers, integrations, messages, validators

# from . import helpers, integrations, messages, models, validators


class Glow(object):

    version = "0.0.0"

    repo = None
    config = None

    current_directory = None
    working_directory = None
    git_directory = None

    glow_config = None

    jira_project_key = None
    github_repository_name = None
    github_token = None

    def _branches(self):
        return [branch.name for branch in self.repo.branches]

    def _branch_exists(self, branch_name):
        return branch_name in self._branches()

    def _pull_branch(self, branch_name, create_branch=False):
        if create_branch:
            self.repo.git.pull("origin", branch_name)
            self.repo.git.checkout("HEAD", b=branch_name)
        else:
            self.repo.git.checkout(branch_name)
            self.repo.git.pull("origin", branch_name)

        messages.success("↓ «{}» pulled.".format(branch_name))

    def _push_branch(self, branch_name):
        self.repo.git.push("origin", branch_name)
        messages.success("↑ «{}» pushed.".format(branch_name))

    def _tags(self):
        return [tag.name for tag in self.repo.tags]

    def _pull_tags(self):
        self.repo.git.fetch("origin", "--tags")
        messages.success("↓ tags pulled.")

    def _push_tags(self):
        self.repo.git.push("origin", "--tags")
        messages.success("↑ tags pushed.")

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
        tags = self._tags()

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

            self._push_tags()
            messages.success(
                "Version {} pushed to remote repository".format(self.version)
            )

        else:
            tags.sort(reverse=True)
            latest = tags[0]
            self.version = semver.VersionInfo.parse(latest)
            messages.log(" :label: Latest version: {}".format(latest))

    def __init__(self):
        """Initialize Github Flow CLI"""

        colorama.init(autoreset=True)

        self._init_repo()
        self._init_glow()
        self._init_version()

    """ Feature methods """

    def start_feature(self, issue_id):
        issue_id = validators.validate_issue_id(issue_id)
        feature_name = "{}-{}".format(self.jira_project_key, issue_id)
        branch_name = "feature/{}".format(feature_name)

        if self._branch_exists(feature_name):
            messages.error("{} already exists locally.".format(branch_name))
            return False

        if integrations.branch_exists(
            self.github_token, self.github_repository_name, branch_name
        ):
            messages.error("{} already exists remotely.".format(branch_name))
            self._pull_branch(branch_name)
            return False

        question = "Start feature name: «{}» [y/n] ".format(branch_name)
        helpers.ask(question)

        commit_sha = integrations.branch_exists(
            self.github_token, self.github_repository_name, "develop"
        )
        commit_ref = "refs/heads/{}".format(branch_name)

        status_code = integrations.create_branch(
            self.github_token,
            self.github_repository_name,
            commit_ref,
            commit_sha,
        )

        if status_code == 201:
            messages.success("New branch: {} created".format(branch_name))
            self._pull_branch(branch_name, create_branch=True)
            messages.success(
                "Switched to a new branch «{}».".format(branch_name)
            )
            return True

        elif status_code == 422:
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
                "Feature branch feature/{} can not be created ({}:).".format(
                    feature_name,
                    status_code,
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

    def start_release(self):
        release_name = self.version.bump_minor()
        # branch_name = "release/{}".format(release_name)
        question = "Start release «{}» [y/n] ".format(release_name)
        helpers.ask(question)

        commit_sha = integrations.branch_exists(
            self.github_token, self.github_repository_name, "develop"
        )
        commit_ref = "refs/heads/release/{}".format(release_name)

        status_code = integrations.create_branch(
            self.github_token,
            self.github_repository_name,
            commit_ref,
            commit_sha,
        )

        if status_code == 201:
            messages.success(
                "New branch: release/{} created".format(release_name)
            )

            if self._pull_branch(
                "release/{}".format(release_name), create_branch=True
            ):
                messages.success(
                    'Switched to a new branch "release/{}".'.format(
                        release_name
                    )
                )
                ...

            else:
                messages.critical(
                    "Unable to checkout to branch: release/{}".format(
                        release_name
                    )
                )
                return False

        elif status_code == 422:
            messages.error(
                "Feature branch release/{} already exists.".format(release_name)
            )
            return False

        else:
            messages.critical(
                "Release branch release/{} can not be created ({}).".format(
                    release_name,
                    status_code,
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
        hotfix_name = self.version.bump_patch()
        # branch_name = "hotfix/{}".format(hotfix_name)
        question = "Start hotfix {} [y/n] ".format(hotfix_name)
        helpers.ask(question)

        commit_sha = integrations.branch_exists(
            self.github_token, self.github_repository_name, "master"
        )
        commit_ref = "refs/heads/hotfix/{}".format(hotfix_name)

        status_code = integrations.create_branch(
            self.github_token,
            self.github_repository_name,
            commit_ref,
            commit_sha,
        )

        if status_code == 201:
            messages.success(
                "New branch: hotfix/{} created".format(hotfix_name)
            )

            if self._pull_branch(
                "hotfix/{}".format(hotfix_name), create_branch=True
            ):
                messages.success(
                    'Switched to a new branch "hotfix/{}".'.format(hotfix_name)
                )
                return True

            else:
                messages.critical(
                    "Unable to checkout to branch: hotfix/{}".format(
                        hotfix_name
                    )
                )
                return False

        elif status_code == 422:
            messages.error(
                "Feature branch hotfix/{} already exists.".format(hotfix_name)
            )
            return False

        else:
            messages.critical(
                "Release branch hotfix/{} can not be created ({}).".format(
                    hotfix_name,
                    status_code,
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
        args = helpers.parse_args()

        method_name = "{}_{}".format(args.action, args.entity)
        methods_names = helpers.get_method_names(self)

        validators.validate_method_name(method_name, methods_names)

        _func = getattr(self, method_name)
        _func(*args.key)


if __name__ == "__main__":
    glow = Glow()
    glow.main()
