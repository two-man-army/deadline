import hashlib, uuid


from django.conf import settings
from django.db import models
from django.db.models import Count
from django.db.models.signals import post_save
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.dispatch import receiver

from rest_framework.authtoken.models import Token

from accounts.helpers import hash_password
from django.db import models
from django.dispatch import receiver


class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)


class User(AbstractBaseUser):
    USERNAME_FIELD = 'email'
    username = models.CharField(max_length=30, unique=True)
    email = models.EmailField(max_length=30, unique=True)
    password = models.CharField(max_length=30)
    score = models.IntegerField(default=0)
    salt = models.CharField(max_length=40)
    role = models.ForeignKey(Role, default=1)
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

    Token.objects.create(user=instance)
    starter_proficiency = Proficiency.objects.filter(needed_percentage=0).first()

    # create a UserSubcategoryProgress for each subcategory and a UserSubcategoryProficiency
    for subcat in SubCategory.objects.all():
        # UserSubcategoryProgress.objects.create(user=instance, subcategory=subcat, user_score=0)
        UserSubcategoryProficiency.objects.create(user=instance, subcategory=subcat, proficiency=starter_proficiency, user_score=0)
