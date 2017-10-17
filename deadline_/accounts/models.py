import hashlib, uuid

import jwt
from django.conf import settings
from django.db import models
from django.db.models import Count
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.dispatch import receiver

from rest_framework.authtoken.models import Token

from accounts.constants import NOTIFICATION_SECRET_KEY
from accounts.errors import UserAlreadyFollowedError, UserNotFollowedError
from accounts.helpers import hash_password, generate_notification_token
from django.db import models
from django.dispatch import receiver

from sql_queries import USER_SELECT_COUNT_OF_SOLVED_CHALLENGES_FOR_SUB_CATEGORY


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)


class User(AbstractBaseUser):
    USERNAME_FIELD = 'email'
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(max_length=30, unique=True)
    password = models.CharField(max_length=256)
    score = models.IntegerField(default=0)
    salt = models.CharField(max_length=40)
    notification_token = models.CharField(max_length=200, null=True)
    users_followed = models.ManyToManyField(to='accounts.User', related_name='followers')
    role = models.ForeignKey(Role)
    last_submit_at = models.DateTimeField(auto_now_add=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Put in an if, since django calls __init__ twice!
        if not self.salt:
            # Store a random salt and hash the password!
            self.salt = uuid.uuid4().hex
            self.password = hash_password(password=self.password, salt=self.salt)

    def __str__(self):
        return self.username

    def fetch_count_of_solved_challenges_for_subcategory(self, sub_category):
        """
        Given a SubCategory object,
            find the number of challenges the user has fully solved from that SubCategory
        """
        from django.db import connection
        from challenges.models import Submission
        challenge_ids_for_category = [c.id for c in sub_category.challenges.all()]
        # TODO: Implement a table to store this logic as calculating it is expensive!

        # temporary hacky solution
        cursor = connection.cursor()
        challenge_id_string = ', '.join(str(p) for p in challenge_ids_for_category)
        if not challenge_id_string:  # EXTREME HACK
            challenge_id_string = '-1'
        cursor.execute(USER_SELECT_COUNT_OF_SOLVED_CHALLENGES_FOR_SUB_CATEGORY.format(challenge_ids=challenge_id_string),
                       (self.id, ))
        solved_challenges_count = cursor.fetchone()[0]

        return solved_challenges_count

    def notification_token_is_expired(self) -> bool:
        """ Checks whether the current token is expired """
        if self.notification_token is None:
            return True
        try:
            jwt.decode(self.notification_token, NOTIFICATION_SECRET_KEY)
            return False
        except jwt.ExpiredSignatureError:
            return True

    def refresh_notification_token(self, force=False):
        if not force and not self.notification_token_is_expired():
            raise Exception("Will not reset the notification token when it is not expired without being forced!")
        self.notification_token = generate_notification_token(self)
        self.save()

    def notification_token_is_valid(self, token):
        return token == self.notification_token and not self.notification_token_is_expired()

    def fetch_newsfeed(self, start_offset=0, end_limit=None):
        """
        Returns all the NewsfeedItems this user should see
        They are a collection of all the NewsfeedItems
            of which the authors are people he has followed
        """
        from social.models.newsfeed_item import NewsfeedItem

        return NewsfeedItem.objects\
            .filter(author_id__in=[us.id for us in self.users_followed.all()] + [self.id])\
            .order_by('-created_at')[start_offset:end_limit]

    def follow(self, user):
        from social.models.notification import Notification

        if user in self.users_followed.all():
            raise UserAlreadyFollowedError(f'{self.username} has already followed {user.username}!')
        Notification.objects.create_receive_follow_notification(recipient=user, follower=self)
        self.users_followed.add(user)

    def unfollow(self, user):
        if user not in self.users_followed.all():
            raise UserNotFollowedError(f'{self.username} has not followed {user.username}!')
        self.users_followed.remove(user)

    def fetch_unsuccessful_challenge_attempts_count(self, challenge: 'Challenge'):
        """
        Returns the count of unsuccessful submissions this user has made for a given challenge
        """
        from challenges.models import Submission
        return (Submission.objects.filter(author_id=self.id, pending=False, challenge_id=challenge.id)
                                  .exclude(result_score=challenge.score)
                                  .count()
                )

    def fetch_max_score_for_challenge(self, challenge_id):
        """
        Fetches the maximum score this user has scored for the given challenge
        """
        from challenges.models import Submission

        top_submission = Submission.fetch_top_submission_for_challenge_and_user(challenge_id, self.id)
        max_score = top_submission.maxscore if top_submission else 0
        return max_score

    def fetch_overall_leaderboard_position(self):
        leaderboard_position = User.objects.all().filter(score__gt=self.score).aggregate(Count('score'))['score__count']
        return leaderboard_position + 1

    @staticmethod
    def fetch_user_count():
        return User.objects.count()

    def fetch_subcategory_proficiency(self, subcategory_id) -> 'UserSubcategoryProficiency':
        """
        Queries the DB and returns the UserSubcategoryProgress model associated with the given subcategory
        """
        from challenges.models import UserSubcategoryProficiency
        usp: UserSubcategoryProficiency = UserSubcategoryProficiency.objects.filter(subcategory_id=subcategory_id).first()
        if usp is None:
            raise Exception(f'Could not find a UserSubcategoryProficiency object for user {self} with subcategory_id {subcategory_id}')
        return usp

    def fetch_proficiency_by_subcategory(self, subcategory_id) -> 'Proficiency':
        """
        Queries the DB and returns a Proficiency object associated with the given user and subcategory
        """
        from challenges.models import UserSubcategoryProficiency
        usp: UserSubcategoryProficiency = UserSubcategoryProficiency.objects\
            .filter(subcategory_id=subcategory_id, user_id=self.id).first()
        if usp is None:
            raise Exception(f'Cound not find a UserSubcategoryProficiency object for user {self} with subcategory_id {subcategory_id}')
        return usp.proficiency

    def get_vote_for_submission(self, submission_id):
        from challenges.models import SubmissionVote
        try:
            return SubmissionVote.objects.get(submission=submission_id, author=self.id)
        except SubmissionVote.DoesNotExist:
            return None


# This code is triggered whenever a new user has been created and saved to the database
@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, *args, **kwargs):
    """
        Create the UserSubcategoryProgress models for each subcategory
            and the Token object
    """
    from challenges.models import SubCategory, UserSubcategoryProficiency, Proficiency
    if not created:
        return

    instance.notification_token = generate_notification_token(instance)
    Token.objects.create(user=instance)
    starter_proficiency = Proficiency.objects.filter(needed_percentage=0).first()

    # create a UserSubcategoryProgress for each subcategory and a UserSubcategoryProficiency
    for subcat in SubCategory.objects.all():
        UserSubcategoryProficiency.objects.create(user=instance, subcategory=subcat, proficiency=starter_proficiency,
                                                  user_score=0)

    instance.save()
