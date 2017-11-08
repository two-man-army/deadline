""" Domain code that is not dependant on the underlying ORM/DB/Framework """
from helpers import get_date_day_difference, datetime_now
from challenges.models import Submission


def submissions_count_by_date_from_user_since(user, since_date) -> dict:
    """
    :return: A dict, counting the number of submissions the user has made for each date
     {
        datetime(2017, 10, 10): 15,
        datetime(2017, 9, 10): 12,
     }
    """
    if get_date_day_difference(datetime_now(), since_date) > 365:
        raise ValueError(f'Querying submissions count per day for more than a year is not supported!')
    submission_data = Submission.fetch_submissions_count_by_day_from_user_since(user, since_date)
    count_data = {}
    for subm_data in submission_data:
        if subm_data['count'] > 0:
            count_data[subm_data['created_at']] = subm_data['count']

    return count_data


def submissions_count_by_month_from_user_since(user, since_date) -> dict:
    """
    :return: A dict, counting the number of submissions the user has made for every month since the given date
    e.g since_date = datetime(2017, 10, 0); today is Jan 2018
     {
        datetime(2017, 10, 0): 200,
        datetime(2017, 11, 0): 300,
        datetime(2017, 12, 0): 100,
        datetime(2018, 01, 0): 123
     }
    """
    if since_date.day != 1:
        raise ValueError(f'{since_date} must be the first day of the month!')
    submission_data = Submission.fetch_submissions_count_by_month_from_user_since(user, since_date)
    count_data = {}
    for subm_data in submission_data:
        if subm_data['count'] > 0:
            count_data[subm_data['month']] = subm_data['count']

    return count_data
