# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import messages


def remove_new_line(stdout):
    """Remove new line from input data"""
    return stdout.replace("\n", "")


def validate_issue_id(issue_id):
    try:
        issue_id = int(issue_id)

    except ValueError:
        messages.critical('IssueID "{}" is not valid.'.format(issue_id))
        sys.exit(1)

    except TypeError:
        messages.critical('IssueID is not set.')
        sys.exit(1)

    return issue_id
