import factory
from challenges.models import ChallengeDescription, Language, Challenge, SubCategory, MainCategory, Submission, User


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('name')
    email = factory.Sequence(lambda n: 'user{0}@somewhere.com'.format(n))
    password = factory.Faker('password')


class MainCategoryFactory(factory.DjangoModelFactory):
    class Meta:
        model = MainCategory

    name = factory.Faker('name')


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
    rating = factory.Faker('random_digit')
    score = factory.Faker('random_digit')
    test_case_count = factory.Faker('random_digit')
    category = factory.SubFactory(SubCategoryFactory)


class SubmissionFactory(factory.DjangoModelFactory):
    class Meta:
        model = Submission

    challenge = factory.SubFactory(ChallengeFactory)
    language = factory.SubFactory(LanguageFactory)
    code = factory.Faker('text')
    task_id = factory.Faker('random_digit')
    result_score = factory.Faker('random_digit')
