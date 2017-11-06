""" Domain code that is not dependant on the underlying ORM/DB/Framework """
from challenges.models import Submission


def submissions_count_by_date_for_user_since(user, since_date) -> dict:
    """
    :return: A dict, counting the number of submissions the user has made for that date
     {
        datetime(2017, 10, 10): 15,
        datetime(2017, 9, 10): 12,
     }
    """
    submission_data = Submission.fetch_submissions_count_from_user_since(user, since_date)
    count_data = {}
    for subm_data in submission_data:
        if subm_data['count'] > 0:
            count_data[subm_data['created_at']] = subm_data['count']

    return count_data
