"""
Code that should be ran only if we are testing code.

This is mostly function that mock others or implement functionality that
    is not present while testing

Everything is called once the AppConfig's ready() function is called,
    indicating that Django has loaded everything, as this AppConfig is added at the end of INSTALLED_APPS
"""
from django.apps import AppConfig


class TestSetupConfig(AppConfig):
    name = 'test_setup'

    def ready(self):
        from django.db.models.signals import post_save
        from challenges.models import Submission

        post_save.connect(create_user_solved_challenges, sender=Submission)


def create_user_solved_challenges(sender, instance: 'Submission', created, *args, **kwargs):
    # Since UserSolvedChallenges is created deep within `run_grader_task`
    #   and in tests it does not get executed at all,
    #   we need a way to create such an object for testing (where we directly create Submissions with max score)
    from copy import deepcopy
    from challenges.models import UserSolvedChallenges

    _has_solved_func = deepcopy(
        instance.has_solved_challenge)  # to not count as a call to the function if its mocked
    if created and _has_solved_func():
        UserSolvedChallenges.objects.create(user=instance.author, challenge=instance.challenge)
