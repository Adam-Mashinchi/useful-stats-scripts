import argparse
import json
import pytz
import requests
from dateutil import parser as date_parser


if __name__ == "__main__":
    print("Running...\n")

    # Only write PR's from _before_ this date!
    utc = pytz.UTC
    compare_date = utc.localize(date_parser.parse("4/3/21 1:23:45.000 PM"))

    # Setup arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
            '--repo', required=True,
            help='''
                Target (remote) GitHub repo. (i.e. "org-name/repo-name")
            ''',
        )
    parser.add_argument(
            '--token', required=True,
            help='''
                GitHub API Token.
            ''',
        )
    parser.add_argument(
            '--branch', default="master",
            help='''
                Target branch of git repo. (Default: "master")
            ''',
        )
    args = parser.parse_args()

    # Define owner/repo names
    owner = args.repo.split('/')[0]
    repo = args.repo.split('/')[-1]
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

    # Setup Requests details
    headers = {
        "Authorization": "token {}".format(args.token)
    }
    payload = {
        "state": "all",
        "direction": "asc",
        "per_page": "100"
    }

    # Variable for all the objects
    all_pull_requests = []

    # Loop variables
    page_counter = 1
    loop = True

    # Loop until you're done with all the pages...
    while loop:
        # Setup which page to call in Requests
        payload['page'] = page_counter
        # Call, and get JSON
        response = requests.get(url, params=payload, headers=headers)
        pull_requests = response.json()
        # Show what page you are on
        print(f"Page {page_counter}")
        # Loop all the Pull Requests you found
        valid_counter = 0
        for pull_request in pull_requests:
            # Compare the updated date, to our global date; if after --> skip
            if date_parser.parse(pull_request['updated_at']) > compare_date:
                continue
            # Otherwise, append it for writing to file ...
            all_pull_requests.append(pull_request)
            # ... and add to valid counter
            valid_counter += 1
        # END for pull_request
        # Show amount of kept PR's in this page
        print(f"{valid_counter}/{len(pull_requests)}")
        # Once we are out of PR's bail
        if len(pull_requests) == 0:
            loop = False
        else:
            # Otherwise, go to next page
            page_counter += 1
        # END for pull_request
    # END WHILE

    # Show total Pull Requests found
    print(f"Total Pull Requests Added: {len(all_pull_requests)}")
    # Write stored ones to file.
    jsonString = json.dumps(all_pull_requests, indent=4)
    repo_name = args.repo.split('/')[-1]
    jsonFile = open(f"BACKFILL.{repo_name}.EXPORT.json", "w")
    jsonFile.write(jsonString)
    jsonFile.close()
    print("DONE!")
    exit()
