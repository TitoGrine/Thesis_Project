from pprint import pprint

from searching import get_initial_users
from discovery import identify_related_profiles


# TODO: Make function to test query results
# TODO: Check problem with score function (all are returning -1.0)

def main():
    ids = get_initial_users()
    related_profiles = identify_related_profiles(ids)

    pprint(related_profiles)


if __name__ == '__main__':
    main()
