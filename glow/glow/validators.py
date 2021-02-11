import sys

from . import messages


def validate_issue_id(issue_id):
    try:
        issue_id = int(issue_id)

    except ValueError:
        messages.critical('IssueID "{}" is not valid.'.format(issue_id))
        sys.exit(1)

    except TypeError:
        messages.critical("IssueID is not set.")
        sys.exit(1)

    return issue_id


def validate_method_name(method_name, methods_names):
    if method_name not in methods_names:
        messages.error(
            "Unknown command «{}»".format(" ".join(method_name.split("_")))
        )
        sys.exit(1)
