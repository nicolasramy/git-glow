def validate_issue_id(issue_id):
    try:
        issue_id = int(issue_id)

    except ValueError:
        return (False, "Issue ID: «{}» is not valid.".format(issue_id))
        
    except TypeError:
        return (False, "IssueID is not set.")
        sys.exit(1)

    return (True, issue_id)