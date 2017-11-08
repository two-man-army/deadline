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
