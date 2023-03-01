import argparse
import json
import logging
import sys
import requests
import re

base_url = "https://github.xxxxxxxxxxxxxx.com"

available_commands = {
    "add_comment": [
        "Adds a single comment for a specified pull request.",
        "Required parameters: organization, repository, token,  pull-request, extras[message]",
    ],
    "add_labels": [
        "Adds a set of labels for a specified pull request.",
        "Required parameters: organization, repository, token, pull-request, extras[labels]",
    ],
    "delete_labels": [
        "Deletes a set of labels for a specified pull request.",
        "Required parameters: organization, repository, token, pull-request, extras[labels]",
    ],
    "dimiss_single_review": [
        "Dismisses a specific review for a specified pull request.",
        "Required parameters: organization, repository, token, pull-request, extras[review_id]",
    ],
    "dismiss_all_reviews": [
        "Dismisses all reviews for a specified pull request.",
        "Required parameters: organization, repository, token, pull-request",
    ],
    "get_commit_message": [
        "Gets a commit message, using the commit_id.",
        "Required parameters: organization, repository, token, pull-request, extras[commit_id]",
    ],
    "label_merged_pr": [
        "Adds and/or deletes a set of labels to a pull_request merged into develop or release.",
        "Required parameters: organization, repository, token, pull-request, extras[commit_id, labels_to_add, labels_to_delete]",
    ],
    "label_prs_mentioned_in_commits": [
        "Adds and/or deletes a set of labels to all PRs mentioned in the commit messages of specified pull_request.",
        "Required parameters: organization, repository, token, pull-request, extras[commit_id, labels_to_add, labels_to_delete]",
    ],
    "list_commits": [
        "Fetches a list of commits for a specified pull request.",
        "Required parameters: organization, repository, token, pull-request",
    ],
    "list_deleted_files": [
        "Fetches a list of deleted files for a specific commit.",
        "Required parameters: organization, repository, token, extras[commit_id]",
    ],
    "fetch_files_from_pr": [
        "Fetches a list of files in a PR",
        "Required parameters: organization, repository, token, pr_number",
    ],
    "pr_approvers": [
        "Fetches a list of approvers in a PR",
        "Required parameters: organization, repository, token, pr_number",
    ],
}
command_template = 'Expected Syntax:\n\tpython3 github_api_call.py -o <Organization Name> -r <Repository> -t <O-Auth Token> -u <Github username> -p <Github password> -l <PR Number> -c <Github API Command> -e \'{"x": "sample", "y": 5, "z": "test}\'\n'


######################
#  HELPER FUNCTIONS  #
######################


def build_headers(token, username, password):
    """Format secret(s) for headers of API call."""
    if token:
        logging.info("Adding comment for token=========")
        logging.info(token)
        headers = {
            "Authorization": f"token { token }",
        }
    elif username and password:
        headers = {"Authorization": f"Basic { username }:{ password }"}
    else:
        raise Exception(
            "Either Authentication Token or Username + Password need to be included in request."
        )
    return headers


def format_epilog():
    """Print available commands at end of help message."""
    epilog = command_template
    epilog += "\n\nAvailable Commands:\n"
    for key in available_commands.keys():
        curr_val = available_commands[key]
        curr_desc = f"\n\t- { key }:\n\t\t{ curr_val[0] }\n\t\t{ curr_val[1] }"
        epilog += curr_desc
    return epilog


def parse_commit_for_pr(commit):
    """
    Returns PR ID, for a given commit message (if exists).
    :param commit: A commit message.
    :type commit: str
    """

    pattern = r"\(#(.+?)\)"
    m = re.search(pattern, commit)
    if m:
        pr_id = m.group(1)
        return pr_id


def is_json(json_str):
    """
    Check if string is json-compatible.
    :param json_str: A json-formattable string.
    :type json_str: str
    """
    try:
        json.loads(json_str)
    except ValueError:
        return False
    return True


def validate_args(args):
    """
    Check the arguments formatting and syntax.
    :param args: Contains arguments passed through command line
    :type args: argparse.Namespace
    """

    if args.token and args.username:
        raise ValueError(
            "ERROR:\tOnly one form of authentication is required (either token or user/pass)."
        )

    if not is_json(args.extras):
        raise ValueError(
            f'\n\nERROR:\tParamater "extras" is not formatted correctly. Incorrect syntax:\n\t{ args.extras }'
        )


######################
#      COMMANDS      #
######################


def fetch_files_from_pr(
    organization,
    token,
    repository,
    pull_request_id,
    username=None,
    password=None,
    **kwargs
):
    """Returns a list of all commit messages for a specified pull request."""
    headers = build_headers(token, username, password)
    curr_endpoint = f"{ base_url }/api/v3/repos/{ organization }/{ repository }/pulls/{ pull_request_id }/files"
    logging.info(f"Fetching files for PR #{ pull_request_id }...")
    response = requests.get(curr_endpoint, headers=headers,)
    commit_dict = json.loads(response.text)
    for files in commit_dict:
        regex = re.compile(r"contents/(.+)[?]")
        val = regex.findall(files["contents_url"])
        file_write = open('pr_file_list.txt', 'a')
        file_write.writelines(val)
        file_write.write("\n")
        file_write.close()
        logging.info(val)
    while 'next' in response.links.keys():
        response = requests.get(response.links['next']['url'], headers=headers,)
        commit_dict = json.loads(response.text)
        for files in commit_dict:
            regex = re.compile(r"contents/(.+)[?]")
            val = regex.findall(files["contents_url"])
            file_write = open('pr_file_list.txt', 'a')
            file_write.writelines(val)
            file_write.write("\n")
            file_write.close()
            logging.info(val)
    logging.info("PR files fetched to file:pr_file_list.txt")

def pr_approvers(
    organization,
    token,
    repository,
    pull_request_id,
    username=None,
    password=None,
    **kwargs
):
    """Returns a list of all approved reviews."""
    headers = build_headers(token, username, password)
    curr_endpoint = f"{ base_url }/api/v3/repos/{ organization }/{ repository }/pulls/8283/reviews"
    logging.info(f"Fetching reviewer for #{ pull_request_id }...")
    response = requests.get(curr_endpoint, headers=headers,)
    reviewer_dict = json.loads(response.text)
    for approver in reviewer_dict:
        if approver["state"] == "APPROVED":
            file_write = open('approver_list.txt', 'a')
            val = approver["user"]["login"]
            if val in ["linkon","RC0003"]:
                file_write.writelines(val)
                file_write.write("\n")
                file_write.close()
                logging.info(val)
    logging.info("Approver list fetched to file:approver_list")



def add_comment(
    organization,
    repository,
    pull_request_id,
    message="automated message via Github API",
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Add a specified comment to a particular pull request."""
    headers = build_headers(token, username, password)
    curr_endpoint = f"{ base_url }/api/v3/repos/{ organization }/{ repository }/issues/{ pull_request_id }/comments"
    if "filename" in kwargs:
        with open(kwargs["filename"], "r") as file:
            message = f"{ message }\n\n\n{ file.read() }"
    logging.info(
        f"Adding comment for PR #{ pull_request_id }...\n\tComment:\n\t'{ message }' "
    )
    response = requests.post(
        curr_endpoint, headers=headers, data=json.dumps({"body": message})
    )
    logging.info(response)


def add_labels(
    organization,
    repository,
    pull_request_id,
    labels=["test"],
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Add a set of labels to a particular pull request."""
    headers = build_headers(token, username, password)
    curr_endpoint = f"{ base_url }/api/v3/repos/{ organization }/{ repository }/issues/{ pull_request_id }/labels"
    logging.info(f"URL: { curr_endpoint }")
    logging.info(
        f"Adding labels for PR #{ pull_request_id }...\n\tLabels:\n\t { ', '.join(labels) }"
    )
    response = requests.post(
        curr_endpoint, headers=headers, data=json.dumps({"labels": labels})
    )
    logging.info(response)


def delete_labels(
    organization,
    repository,
    pull_request_id,
    labels=["test"],
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Deletes a set of specified labels from a particular pull request."""
    headers = build_headers(token, username, password)
    curr_endpoint = f"{ base_url }/api/v3/repos/{ organization }/{ repository }/issues/{ pull_request_id }/labels"
    logging.info(f"URL: { curr_endpoint }")
    logging.info(
        f"Removing labels for PR #{ pull_request_id }...\n\tLabels:\n\t { ', '.join(labels) }"
    )
    for label in labels:
        response = requests.delete(f"{curr_endpoint}/{label}", headers=headers,)
        logging.info(f"Label: {label}\n\tResponse: {response}")


def dismiss_single_review(
    organization,
    repository,
    pull_request_id,
    review_id,
    message="automated dismissal via Github API",
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Dismiss a specified review for a particular pull request."""
    headers = build_headers(token, username, password)
    curr_endpoint = f"{ base_url }/api/v3/repos/{ organization }/{ repository }/pulls/{ pull_request_id }/reviews/{ review_id }/dismissals"
    logging.info(f"Dismissing Review '{ review_id }' for PR #{ pull_request_id }")
    response = requests.put(
        curr_endpoint, headers=headers, data=json.dumps({"message": message})
    )
    logging.info(response)


def dismiss_all_reviews(
    organization,
    repository,
    pull_request_id,
    message="automated dismissal via Github API",
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Dismiss all reviews for a particular pull request."""
    headers = build_headers(token, username, password)
    logging.info(
        f"Fetching list of reviews for { organization }/{ repository }/{ pull_request_id }."
    )
    response = requests.get(
        f"{ base_url }/api/v3/repos/{ organization }/{ repository }/pulls/{ pull_request_id }/reviews",
        headers=headers,
    )
    body = json.loads(response.text)
    review_ids = []
    for review in body:
        if "id" in review:
            curr_id = review["id"]
            logging.info(f"current ID: { curr_id }")
            review_ids.append(curr_id)

    logging.info(
        f"Dismissing all reviews by ID for { organization }/{ repository }/{ pull_request_id }."
    )
    for review_id in review_ids:
        dismiss_single_review(
            organization, repository, token, pull_request_id, review_id
        )


def get_commit_message(
    organization,
    repository,
    commit_id,
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Gets a commit message, using the commit_id."""
    headers = build_headers(token, username, password)
    curr_endpoint = f"{ base_url }/api/v3/repos/{ organization }/{ repository }/commits/{ commit_id }"
    response = requests.get(curr_endpoint, headers=headers,)
    json_response = json.loads(response.text)
    commit_message = json_response["commit"]["message"]
    logging.info(commit_message)
    return commit_message


def get_pr_id_from_commit_id(
    organization,
    repository,
    commit_id,
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Gets a pull_request id, by parsing commit for (#xxx)."""
    commit_message = get_commit_message(
        organization=organization,
        repository=repository,
        commit_id=commit_id,
        token=token,
        username=username,
        password=password,
    )
    pr_id = parse_commit_for_pr(commit_message)
    logging.info(pr_id)
    return pr_id


def label_merged_pr(
    organization,
    repository,
    commit_id,
    labels_to_add=["release"],
    labels_to_delete=["in_development"],
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Adds and/or deletes a set of labels for a pull_request (which was merged into develop or release)."""
    commit_message = get_commit_message(
        organization=organization,
        repository=repository,
        commit_id=commit_id,
        token=token,
        username=username,
        password=password,
    )
    pr_id = parse_commit_for_pr(commit_message)
    logging.info(f"PR IDs parsed from commit:\n\t{pr_id}")
    if pr_id:
        add_labels(
            organization=organization,
            repository=repository,
            pull_request_id=pr_id,
            labels=labels_to_add,
            token=token,
            username=username,
            password=password,
        )
        delete_labels(
            organization=organization,
            repository=repository,
            pull_request_id=pr_id,
            labels=labels_to_delete,
            token=token,
            username=username,
            password=password,
        )


def label_prs_mentioned_in_commits(
    organization,
    repository,
    pull_request_id=None,
    commit_id=None,
    labels_to_add=["deployed"],
    labels_to_delete=["undeployed"],
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Adds and/or deletes a set of labels to all PRs mentioned in the commit messages of specified pull_request."""
    if pull_request_id is None:
        pull_request_id = get_pr_id_from_commit_id(
            organization=organization,
            repository=repository,
            commit_id=commit_id,
            token=token,
            username=username,
            password=password,
        )

    commits = list_commits(
        organization=organization,
        repository=repository,
        pull_request_id=pull_request_id,
        token=token,
        username=username,
        password=password,
    )
    dirty_pr_ids = [parse_commit_for_pr(commit) for commit in commits]
    pr_ids = [pr_id for pr_id in dirty_pr_ids if pr_id]
    logging.info(f"PR IDs parsed from commits:\n\t{pr_ids}")

    for pr_id in pr_ids:
        add_labels(
            organization=organization,
            repository=repository,
            pull_request_id=pr_id,
            labels=labels_to_add,
            token=token,
            username=username,
            password=password,
        )
        delete_labels(
            organization=organization,
            repository=repository,
            pull_request_id=pr_id,
            labels=labels_to_delete,
            token=token,
            username=username,
            password=password,
        )


def list_commits(
    organization,
    repository,
    pull_request_id,
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Returns a list of all commit messages for a specified pull request."""
    headers = build_headers(token, username, password)
    curr_endpoint = f"{ base_url }/api/v3/repos/{ organization }/{ repository }/pulls/{ pull_request_id }/commits"
    logging.info(f"Fetching commits for PR #{ pull_request_id }...")
    response = requests.get(curr_endpoint, headers=headers,)
    commit_dict = json.loads(response.text)
    commit_messages = []
    for commit in commit_dict:
        commit_messages.append(str(commit["commit"]["message"]))
    logging.info(f"Commit Messages:\n\t{commit_messages}")
    return commit_messages


def list_deleted_files(
    organization,
    repository,
    commit_id,
    token=None,
    username=None,
    password=None,
    **kwargs,
):
    """Gets a list of files deleted from a commit, using the commit_id."""
    headers = build_headers(token, username, password)
    curr_endpoint = f"{ base_url }/api/v3/repos/{ organization }/{ repository }/commits/{ commit_id }"
    response = requests.get(curr_endpoint, headers=headers,)
    json_response = json.loads(response.text)
    logging.info(json_response)
    files_modified = json_response["files"]
    deleted_files = []
    logging.info("\n\nRaw dump of json response:")
    logging.info(json.dumps(files_modified, indent=4, sort_keys=True))
    logging.info("\n\nList of all files modified:")
    for file in files_modified:
        file_name = file["filename"]
        status = file["status"]
        logging.info(f"Filename: {file_name}. Status: {status}")

    logging.info("\n\nExplanation of what's being deleted:")
    # Only delete files if they have been renamed or removed
    for file in files_modified:
        file_name = file["filename"]
        status = file["status"]
        if status == "removed":
            deleted_files.append(file_name)
            logging.info(f"Deleting {file_name}.")
        if status == "renamed":
            old_file_name = file["previous_filename"]
            logging.info(f"Deleting {old_file_name} (renamed to {file_name})")
            deleted_files.append(old_file_name)
    logging.info("\n\n List of files to be deleted:\n" + "\n".join(deleted_files))
    return deleted_files


def main(argv):
    """
    Parses input arguments and formats parameters for generating specified command (API request).
    On error: prints expected syntax, list of commands, and error details.
    """
    parser = argparse.ArgumentParser(
        prog="github_api_call",
        formatter_class=argparse.RawTextHelpFormatter,
        description="A python script that handles GitHub API calls.",
        epilog=format_epilog(),
    )

    parser.add_argument(
        "-o", "--organization", type=str, help="Owner of GitHub repository."
    )
    parser.add_argument(
        "-r", "--repository", type=str, help="Name of the GitHub repository."
    )
    parser.add_argument(
        "-t", "--token", type=str, help="User's GitHub Personal Access Token."
    )
    parser.add_argument(
        "-u", "--username", "--user", type=str, help="User's GitHub username."
    )
    parser.add_argument(
        "-p", "--password", "--pass", type=str, help="User's Github password."
    )
    parser.add_argument(
        "-l",
        "--pull_request_id",
        "--pull-request",
        type=str,
        help="The issue # of the Pull Request.",
    )
    parser.add_argument(
        "-c",
        "--command",
        type=str,
        help="Name of python function associated with API call being made.",
    )
    parser.add_argument(
        "-e", "--extras", type=str, help="Extra dictionary to allow for more arguments."
    )

    args = parser.parse_args()
    validate_args(args)

    parameters = {**vars(args), **json.loads(args.extras)}
    pretty_params = "\n".join(
        [f"{key:<20} {value}" for key, value in parameters.items()]
    )
    logging.info(f"\n\nParsed Parameters:\n{ pretty_params }")
    logging.info("\n\n\n")

    return globals()[args.command](**parameters)


if __name__ == "__main__":
    logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
    print(main(sys.argv[1:]))
