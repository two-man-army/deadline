import factory
from random import choice, randint

from accounts.models import Role, UserPersonalDetails
from challenges.models import ChallengeDescription, Language, Challenge, SubCategory, MainCategory, Submission, User, \
    SubmissionComment, Proficiency, ChallengeComment


class CustomFaker:
    @staticmethod
    def school():
        return choice(['Harvard', 'Berkeley', 'Stanford'])

    @staticmethod
    def school_major():
        return 'Computer Science'

    @staticmethod
    def facebook_profile_link():
        return f'www.facebook.com/{factory.Faker("user_name").generate({})}'[:50]

    @staticmethod
    def github_profile_link():
        return f'www.github.com/{factory.Faker("user_name").generate({})}'[:50]

    @staticmethod
    def twitter_profile_link():
        return f'www.twitter.com/{factory.Faker("user_name").generate({})}'[:50]

    @staticmethod
    def linkedin_profile_link():
        return f'www.linkedin.com/in/{factory.Faker("user_name").generate({})}'[:50]

    @staticmethod
    def interests():
        random_interests = [
            'mountain climbing', 'mountaing biking',
            'professional gaming', 'gambling', 'working out',
            'football', 'soccer', 'baseball', 'coding', 'drawing',
            'working'
        ]
        interests = []
        for i in range(randint(0, 5)):
            interests.append(choice(random_interests))

        return interests

    @staticmethod
    def country():
        return factory.Faker('country').generate({})[:35]


class RoleFactory(factory.DjangoModelFactory):
    class Meta:
        model = Role
    name = factory.Faker('name')


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('name')
    email = factory.Sequence(lambda n: 'user{0}@somewhere.com'.format(n))
    password = factory.Faker('password')
    role = factory.SubFactory(RoleFactory)


class UserPersonalDetailsFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserPersonalDetails

    user = factory.SubFactory(UserFactory)
    about = factory.Faker('text')
    country = CustomFaker.country()
    city = factory.Faker('city')
    school = factory.LazyFunction(CustomFaker.school)
    school_major = factory.LazyFunction(CustomFaker.school_major)
    job_company = factory.Faker('company')
    job_title = factory.Faker('job')
    personal_website = factory.Faker('uri')
    interests = factory.LazyFunction(CustomFaker.interests)
    facebook_profile = factory.LazyFunction(CustomFaker.facebook_profile_link)
    github_profile = factory.LazyFunction(CustomFaker.github_profile_link)
    twitter_profile = factory.LazyFunction(CustomFaker.twitter_profile_link)
    linkedin_profile = factory.LazyFunction(CustomFaker.linkedin_profile_link)


class MainCategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = MainCategory

    name = factory.Faker('name')


class ProficiencyFactory(factory.DjangoModelFactory):
    class Meta:
        model = Proficiency

    name = factory.Faker('name')
    needed_percentage = factory.Faker('random_digit')


class SubCategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = SubCategory

    name = factory.Faker('name')
    meta_category = factory.SubFactory(MainCategoryFactory)


class ChallengeDescFactory(factory.DjangoModelFactory):
    class Meta:
        model = ChallengeDescription

    content = factory.Faker('sentence')


class LanguageFactory(factory.DjangoModelFactory):
    class Meta:
        model = Language

    name = factory.Sequence(lambda n: 'LANG{0}'.format(n))


class ChallengeFactory(factory.DjangoModelFactory):
    class Meta:
        model = Challenge

    name= factory.Sequence(lambda n: 'CHALLENGE {0}'.format(n))
    description = factory.SubFactory(ChallengeDescFactory)
    difficulty = factory.Faker('random_digit')
    score = factory.Faker('random_digit')
    test_case_count = factory.Faker('random_digit')
    category = factory.SubFactory(SubCategoryFactory)


class ChallengeCommentFactory(factory.DjangoModelFactory):
    class Meta:
        model = ChallengeComment

    challenge = factory.SubFactory(ChallengeFactory)
    author = factory.SubFactory(UserFactory)
    content = factory.Faker('text')


class SubmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Submission

    challenge = factory.SubFactory(ChallengeFactory)
    language = factory.SubFactory(LanguageFactory)
    code = factory.Faker('text')
    task_id = factory.Faker('random_digit')
    result_score = factory.Faker('random_digit')


class SubmissionCommentFactory(factory.DjangoModelFactory):
    class Meta:
        model = SubmissionComment

    content = factory.Faker('text')
    submission = factory.SubFactory(SubmissionFactory)
    author = factory.SubFactory(UserFactory)
