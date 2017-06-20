import factory

from education.models import HomeworkTaskDescription


class HomeworkTaskDescriptionFactory(factory.DjangoModelFactory):
    class Meta:
        model = HomeworkTaskDescription

    content = factory.Faker('sentence')
    input_format = factory.Faker('sentence')
    output_format = factory.Faker('sentence')
    constraints = factory.Faker('sentence')
    sample_input = factory.Faker('sentence')
    sample_output = factory.Faker('sentence')
    explanation = factory.Faker('sentence')
