from accounts.models import User, Role
from challenges.models import Language, MainCategory, SubCategory, Challenge, Submission, Proficiency, UserSubcategoryProficiency
from challenges.tests.factories import ChallengeDescFactory


class TestHelperMixin:
    """
    A Mixin class providing some commonly used helper functions
    """
    def create_user_and_auth_token(self):
        """
        Creates a user model and token, attaching them to self
        """
        # check if role exists
        self.base_role = Role.objects.filter(name='User').first()
        if self.base_role is None:
            self.base_role = Role.objects.create(name='User')

        self.auth_user = User.objects.create(username='123', password='123', email='123@abv.bg', score=123, role=self.base_role)
        self.auth_token = 'Token {}'.format(self.auth_user.auth_token.key)

    def base_set_up(self):
        """
        Since a lot of tests use the same setUp code, namely creating:
            - A user
            - A submission
            - A challenge (and everything associated with it, subcategory, proficiency, etc)
        This function encapsulates it
        """
        self.sample_desc = ChallengeDescFactory()
        self.python_language = Language.objects.create(name="Python")
        challenge_cat = MainCategory.objects.create(name='Tests')
        self.sub_cat = SubCategory.objects.create(name='tests', meta_category=challenge_cat)
        Proficiency.objects.create(name='starter', needed_percentage=0)

        self.challenge = Challenge.objects.create(name='Hello', difficulty=5, score=10, description=self.sample_desc,
                                                  test_case_count=2, category=self.sub_cat)
        self.challenge.supported_languages.add(self.python_language)
        self.challenge.save()
        self.challenge_name = self.challenge.name

        self.create_user_and_auth_token()
        self.subcategory_progress = UserSubcategoryProficiency.objects.filter(subcategory=self.sub_cat,
                                                                              user=self.auth_user).first()
        self.submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                    author=self.auth_user, code="")
