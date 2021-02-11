import errno
import os
import sys

import colorama
from git import Repo
from git.exc import InvalidGitRepositoryError
import semver

from . import helpers, integrations, messages, validators


class Glow(object):

    version = "0.0.0"

    repo = None
    config = None

    current_directory = None
    working_directory = None
    git_directory = None

    jira_project_key = None
    github_repository_name = None
    github_token = None

    def _branches(self):
        return [branch.name for branch in self.repo.branches]

    def _branch_exists(self, branch_name):
        return branch_name in self._branches()

    def _change_branch(self, branch_name):
        return self.repo.git.checkout(branch_name)

    def _rebase_branch(self, branch_name):
        return self.repo.git.rebase(branch_name)

    def _pull_branch(self, branch_name, create=False):
        if create:
            self.repo.git.checkout("-b", branch_name)

        else:
            self.repo.git.checkout(branch_name)

        self.repo.git.pull("origin", branch_name)

        messages.success("↓ «{}» pulled.".format(branch_name))

    def _push_branch(self, branch_name, force=False):
        if force:
            self.repo.git.push("origin", branch_name, "--force")

        else:
            self.repo.git.push("origin", branch_name)

        messages.info("↑ «{}» pushed.".format(branch_name))

    def _tags(self):
        return [tag.name for tag in self.repo.tags]

    def _create_tag(self, version, ref=None):
        if ref:
            return self.repo.create_tag(version, ref=ref)
        else:
            return self.repo.create_tag(version)

    def _pull_tags(self):
        self.repo.git.fetch("origin", "--tags")
        messages.success("↓ tags pulled.")

    def _push_tags(self):
        self.repo.git.push("origin", "--tags")
        messages.info("↑ tags pushed.")

    def _get_changes(self, source_branch, dest_branch):
        return self.repo.git.log(
            "{}...{}".format(source_branch, dest_branch), "--pretty=format:%s"
        )

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

            self._create_tag(self.version, first_commit)

            self._push_tags()
            messages.success(
                "Version {} pushed to remote repository".format(self.version)
            )

        else:
            tags.sort(reverse=True)
            latest = tags[0]
            self.version = semver.VersionInfo.parse(latest)
            messages.log(":label:  Latest version: {}".format(latest))

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

        if self._branch_exists(branch_name):
            messages.error("«{}» already exists locally.".format(branch_name))
            return False

        if integrations.branch_exists(
            self.github_token, self.github_repository_name, branch_name
        ):
            messages.warning(
                "«{}» already exists remotely.".format(branch_name)
            )
            self._pull_branch(branch_name, create=True)
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
            messages.success("«{}» created on Github".format(branch_name))
            self._pull_branch(branch_name, create=True)
            messages.success("Switch to «{}».".format(branch_name))
            return True

        elif status_code == 422:
            messages.warning("{} already exists on Github.".format(branch_name))
            self._pull_branch(branch_name)
            messages.success("Switch to «{}».".format(branch_name))
            return True

        else:
            messages.critical(
                "{} can not be created on Github ({}:).".format(
                    branch_name,
                    status_code,
                )
            )
            return False

    def review_feature(self, issue_id):
        issue_id = validators.validate_issue_id(issue_id)
        feature_name = "{}-{}".format(self.jira_project_key, issue_id)
        branch_name = "feature/{}".format(feature_name)

        if not self._branch_exists(branch_name):
            messages.error("«{}» doesn't exists locally.".format(branch_name))
            return False

        if not integrations.branch_exists(
            self.github_token, self.github_repository_name, branch_name
        ):
            messages.error("«{}» doesn't exists remotely.".format(branch_name))
            return False

        self._change_branch("develop")
        self._pull_branch("develop")

        self._change_branch(branch_name)
        self._rebase_branch("develop")
        self._push_branch(branch_name, force=True)

        changes = self._get_changes(branch_name, "develop")

        status_code, response = integrations.create_pull_request(
            self.github_token,
            self.github_repository_name,
            branch_name,
            "develop",
            feature_name,
            changes,
        )

        if status_code == 201:
            messages.success("New PR created: {}".format(response))
            return True

        else:
            for error in response:
                messages.critical(error)
            return False

    def cancel_feature(self, issue_id, description=None):
        messages.warning("Not implemented yet")

    """ Release methods """

    def start_release(self):
        release_name = self.version.bump_minor()
        branch_name = "release/{}".format(release_name)

        hotfix_name = self.version.bump_patch()
        hotfix_branch_name = "hotfix/{}".format(hotfix_name)

        if self._branch_exists(branch_name):
            messages.error("«{}» already exists locally.".format(branch_name))
            return False

        if integrations.branch_exists(
            self.github_token, self.github_repository_name, branch_name
        ):
            messages.warning(
                "«{}» already exists remotely.".format(branch_name)
            )
            self._pull_branch(branch_name, create=True)
            return False

        if integrations.branch_exists(
            self.github_token, self.github_repository_name, hotfix_branch_name
        ):
            messages.critical(
                "An hotfix «{}» is running...".format(hotfix_branch_name)
            )
            return False

        question = "Start release «{}» [y/n] ".format(release_name)
        helpers.ask(question)

        self._pull_branch("develop")

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
            messages.success("«{}» created on Github".format(branch_name))
            self._pull_branch(branch_name, create=True)
            messages.success("Switch to «{}».".format(branch_name))
            return True

        elif status_code == 422:
            messages.warning("{} already exists on Github.".format(branch_name))
            self._pull_branch(branch_name, create=True)
            messages.success("Switch to «{}».".format(branch_name))
            return True

        else:
            messages.critical(
                "{} can not be created on Github ({}:).".format(
                    branch_name,
                    status_code,
                )
            )
            return False

    def review_release(self):
        release_name = self.version.bump_minor()
        branch_name = "release/{}".format(release_name)

        if not self._branch_exists(branch_name):
            messages.error("«{}» doesn't exists locally.".format(branch_name))
            return False

        if not integrations.branch_exists(
            self.github_token, self.github_repository_name, branch_name
        ):
            messages.error("«{}» doesn't exists remotely.".format(branch_name))
            return False

        self._change_branch("main")
        self._pull_branch("main")

        self._change_branch(branch_name)
        self._rebase_branch("develop")
        self._push_branch(branch_name, force=True)

        changes = self._get_changes(branch_name, "main")

        status_code, response = integrations.create_pull_request(
            self.github_token,
            self.github_repository_name,
            branch_name,
            "main",
            str(release_name),
            changes,
        )

        if status_code == 201:
            messages.success("New PR created: {}".format(response))
            return True

        else:
            for error in response:
                messages.error(error)
            return False

    def finish_release(self):
        release_name = self.version.bump_minor()
        branch_name = "release/{}".format(release_name)

        if not self._branch_exists(branch_name):
            messages.error("«{}» doesn't exists locally.".format(branch_name))
            return False

        if not integrations.branch_exists(
            self.github_token, self.github_repository_name, branch_name
        ):
            messages.error("«{}» doesn't exists remotely.".format(branch_name))
            return False

        self._change_branch("main")
        self._pull_branch("main")

        self._create_tag(str(release_name))

        self._change_branch("develop")
        self._pull_branch("develop")

        self.repo.git.merge("--no-ff", branch_name)
        self.repo.git.branch("-D", branch_name)
        self.repo.git.push("origin", ":{}".format(branch_name))
        self.repo.git.remote("prune", "origin")

        self._push_tags()
        messages.success("«{}» finished :fireworks:.".format(branch_name))

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
