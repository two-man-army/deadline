import json

from accounts.models import User, Role
from challenges.models import Language, MainCategory, SubCategory, Challenge, Submission, Proficiency, UserSubcategoryProficiency
from challenges.tests.factories import ChallengeDescFactory


class TestHelperMixin:
    """
    A Mixin class providing some commonly used helper functions
    """

    def assertEqualHStore(self, a, b, dict_fields: [str]=[]):
        """
            Asserts that two DB HStore fields are equal.
            Accepts all the inner dictionary fields in the HStore and parses them into a dictionary
            This is needed because if we have an HStore with a dictionary field.
                e.g hstore = { "notif_content": {"yo": "yo"} }
                The inner dictionary field gets converted to a string in the DB
                    and when queried back is received as a string.
                This screws up the assertEqual, as you're comparing a string to a dict.
            Same thing with Integer fields
        """
        for field in [a, b]:
            for key, val in field.items():
                if key in dict_fields and not isinstance(val, dict):
                    field[key] = json.loads(field[key].replace("'", '"'))
                elif isinstance(val, str):  # try to parse into an integer
                    try:
                        field[key] = int(field[key])
                    except ValueError:
                        pass
        self.assertEqual(a, b)

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

    def base_set_up(self, create_user=True):
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
        if create_user:
            self.create_user_and_auth_token()
        self.subcategory_progress = UserSubcategoryProficiency.objects.filter(subcategory=self.sub_cat,
                                                                              user=self.auth_user).first()
        self.submission = Submission.objects.create(language=self.python_language, challenge=self.challenge,
                                                    author=self.auth_user, code="")

    def create_challenge(self) -> Challenge:
        """
        Creates a Challenge object and returns it
        """
        from random import randint
        if not SubCategory.objects.exists():
            # create a subcategory
            if not MainCategory.objects.exists():
                main_cat = MainCategory.objects.create(name=f'Tests{randint(1, 100)}')
            else:
                main_cat = MainCategory.objects.first()
            sub_cat = SubCategory.objects.create(name='tests', meta_category=main_cat)
        else:
            sub_cat = SubCategory.objects.first()

        return Challenge.objects.create(name=f'Sample Challenge{randint(1, 100)}', difficulty=randint(1, 10),
                                        score=randint(1, 100), description=ChallengeDescFactory(),
                                        test_case_count=randint(1, 20), category=sub_cat)

    def setup_proficiencies(self):
        """
        Creates a couple of Proficiency models
        """
        Proficiency.objects.create(name='starter', needed_percentage=0)
        Proficiency.objects.create(name='newb', needed_percentage=25)
        Proficiency.objects.create(name='med', needed_percentage=50)
        Proficiency.objects.create(name='advanced', needed_percentage=75)
        Proficiency.objects.create(name='master', needed_percentage=100)
