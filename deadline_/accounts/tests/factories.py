import factory
from accounts.models import User


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('name')
    email = factory.Sequence(lambda n: 'user{0}@somewhere.com'.format(n))
    password = factory.Faker('password')