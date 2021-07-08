import argparse
import csv
import os
from collections import OrderedDict
from datetime import datetime
from github import Github


def write_to_csv_file(target_file, row_data, write_type='a'):
    with open(target_file, write_type, encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=',')
        writer.writerow(row_data)
    return True


if __name__ == "__main__":
    print("Running...\n")

    # Variable to let us know how long this takes...
    begin_time = datetime.now()

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

    # Setup GitHub connection
    g = Github(login_or_token=args.token, per_page=100)
    repo = g.get_repo(args.repo)

    # Define object to return
    monthly_stats = {}
    # Place to store all users when they first pull
    pull_authors = {
        "all": [],
        "new": {}
    }
    # Object for author stats
    monthly_author_stats = {}

    # Loop all the closed PR's, oldest-to-newest
    for pull in repo.get_pulls('closed', direction="asc", base=args.branch):
        # Skip if not merged
        if pull.merged is False:
            continue

        # Set the current month
        current_month = pull.merged_at.strftime("%Y-%m")

        # See if month exists in object; if not, create it.
        if monthly_stats.get(current_month, False) is False:
            monthly_stats[current_month] = {
                "pull_requests": 0,
                "new_contributors": 0,
                "total_contributors": 0
            }
        # END if monthly_stats.get

        # Add to "new author" counter, if never seen before
        if pull.user.login not in pull_authors["all"]:
            monthly_stats[current_month]["new_contributors"] += 1
            pull_authors["all"].append(pull.user.login)

            # Make sure we have an object for this month
            if pull_authors["new"].get(current_month, False) is False:
                pull_authors["new"][current_month] = []
            # END if pull_authors["new"]

            # Add them to a list for output later
            pull_authors["new"][current_month].append(pull.user.login)
        # END if pull.user.login

        # Add to pull counter
        monthly_stats[current_month]["pull_requests"] += 1

        # Now setup the monthly author stats
        # See if month exists in object; if not, create it.
        if monthly_author_stats.get(current_month, False) is False:
            monthly_author_stats[current_month] = {}
        if pull.user.login not in monthly_author_stats[current_month]:
            monthly_author_stats[current_month][pull.user.login] = 0
        # Add to counter
        monthly_author_stats[current_month][pull.user.login] += 1
        # END if monthly_author_stats.get

        # END if pull.merged
    # END for pull

    # TODO: figure out why we have to sort the list for some reason ...
    pull_authors_ordered = OrderedDict(
        sorted(pull_authors["new"].items(), key=lambda t: t[0])
        )
    pull_authors["new"] = pull_authors_ordered

    # Output the New Authors by month
    # Need a running tally of all authors
    total_authors = 0
    for month in pull_authors["new"]:
        # Add this month's new Authors to tally
        total_authors += len(pull_authors["new"][month])
        # Set that value in this month's data
        monthly_stats[month]['total_contributors'] = total_authors
        # Print out the month, with some stats
        print("\n---%s--- (%s/%s)" % (
            month,
            len(pull_authors["new"][month]),
            total_authors
        ))
        # Print out the new authors
        for author in pull_authors["new"][month]:
            print(author)
        # END for author
    # END for month

    # Output the general monthly stats
    # Define CSV name
    csv_name_unique = "%s.github_monthly_stats.%s.csv" % (
        args.repo.split('/')[-1],
        datetime.now().strftime('%Y%m%d_%H%M')
    )
    # Create first row of CSV
    first_row = [
        "Month", "Pull Requests",
        "New Contributors",
        "Total Contributors"
        ]
    write_to_csv_file(csv_name_unique, first_row, write_type="w")
    # For each month, write data
    for month in monthly_stats:
        unique_row_to_write = [month]
        for attr in monthly_stats[month]:
            unique_row_to_write.append(monthly_stats[month][attr])
        # END for attr
        write_to_csv_file(csv_name_unique, unique_row_to_write)
    # END for month

    # Display where the CSV file is
    print("\n\nCreated file:\n\t%s/%s" % (
        os.getcwd(), csv_name_unique
    ))

    # Output the monthly author
    # Define CSV name
    csv_name_unique = "%s.github_author_stats.%s.csv" % (
        args.repo.split('/')[-1],
        datetime.now().strftime('%Y%m%d_%H%M')
    )
    # Create first row of CSV
    first_row = [
        "Month", "Author", "Pull Requests"
        ]
    write_to_csv_file(csv_name_unique, first_row, write_type="w")
    # For each month, write data
    for month in monthly_author_stats:
        for author in monthly_author_stats[month]:
            # print(month)
            # print(author)
            # print(monthly_author_stats[month][author])
            write_to_csv_file(csv_name_unique, [
                month, author,
                monthly_author_stats[month][author]
            ])
        # END for author
    # END for month

    # Display where the CSV file is
    print("\n\nCreated file:\n\t%s/%s" % (
        os.getcwd(), csv_name_unique
    ))

    print("DONE!")
    # How long did this take?
    print(datetime.now() - begin_time)
    exit()
