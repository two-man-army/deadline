from rest_framework import serializers

from education.models import Course, HomeworkTaskDescription, HomeworkTask
from challenges.models import Language


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ('name', 'difficulty', 'languages')


class HomeworkTaskDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkTaskDescription
        exclude = ('id', )


class HomeworkTaskSerializer(serializers.ModelSerializer):
    description = HomeworkTaskDescriptionSerializer()

    class Meta:
        model = HomeworkTask
        exclude = ('test_case_count', )

    def create(self, validated_data):
        description_data = validated_data.pop('description')
        description_ser = HomeworkTaskDescriptionSerializer(data=description_data)
        if not description_ser.is_valid():
            raise Exception('Could not serialize the given description!')
        description = description_ser.save()
        validated_data['description'] = description

        return super().create(validated_data)

    @property
    def data(self):
        """
            Attach the Language's name in the deserialization
             This is SQL-expensive and I will probably curse myself later on for adding this.
             You can always speed it up by building the language IDs and doing one SQL query
            Also attach the test_case_count
        """
        loaded_data = super().data
        hw_task = HomeworkTask.objects.get(id=loaded_data['id'])
        loaded_data['supported_languages'] = [Language.objects.get(id=lang_id).name for lang_id in loaded_data['supported_languages']]
        loaded_data['test_case_count'] = hw_task.test_case_count

        return loaded_data
