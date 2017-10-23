from rest_framework import serializers

from education.models import Course, HomeworkTaskDescription, HomeworkTask, Lesson, Homework, TaskSubmission, \
    TaskTestCase
from challenges.models import Language


class CourseSerializer(serializers.ModelSerializer):
    teachers = serializers.SerializerMethodField()
    lessons = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ('name', 'difficulty', 'languages', 'main_teacher', 'teachers', 'lessons')

    def get_teachers(self, obj):
        return [{'name': teacher.username, 'id': teacher.id} for teacher in obj.teachers.all()]

    def get_lessons(self, obj):
        return [{'consecutive_number': lesson.lesson_number, 'short_description': lesson.intro} for lesson in obj.lessons.all()]

    def to_representation(self, instance):
        repr = super().to_representation(instance)

        repr['main_teacher'] = {'name': self.instance.main_teacher.username, 'id': self.instance.main_teacher.id}
        repr['languages'] = [lang.name for lang in self.instance.languages.all()]

        return repr


class HomeworkTaskDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HomeworkTaskDescription
        exclude = ('id', )


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'

    def create(self, validated_data):
        # TODO: move to helper method
        validated_data['lesson_number'] = validated_data['course'].lessons.count() + 1
        validated_data['is_under_construction'] = True
        return super().create(validated_data)

    def is_valid(self, raise_exception=False):
        self.initial_data['lesson_number'] = -1  # Temporary
        return super().is_valid(raise_exception=raise_exception)


class HomeworkTaskSerializer(serializers.ModelSerializer):
    description = HomeworkTaskDescriptionSerializer()
    test_case_count = serializers.SerializerMethodField()

    class Meta:
        model = HomeworkTask
        fields = '__all__'
        non_editable_fields = ('homework', 'supported_languages')

    def create(self, validated_data):
        description_data = validated_data.pop('description')
        description_ser = HomeworkTaskDescriptionSerializer(data=description_data)
        if not description_ser.is_valid():
            raise Exception('Could not serialize the given description!')
        description = description_ser.save()
        validated_data['description'] = description
        validated_data['is_under_construction'] = True  # always is_under_construction on creation

        return super().create(validated_data)

    def update(self, instance, validated_data):
        description = None
        if 'description' in validated_data:
            description = validated_data.pop('description')
        # TODO: can be a decorator
        for non_editable_field in self.Meta.non_editable_fields:
            if non_editable_field in validated_data:
                validated_data.pop(non_editable_field)

        updated_task = super().update(instance, validated_data)

        if description is not None:
            # update the description as well
            desc_serializer = HomeworkTaskDescriptionSerializer(updated_task.description, description)
            if desc_serializer.is_valid():
                desc_serializer.save()
        # TESTME: Might update task but fail to update description? We might want atomic behavior here

        return updated_task

    def get_test_case_count(self, obj):
        return obj.test_case_count

    @property
    def data(self):
        """
            Attach the Language's name in the deserialization
             This is SQL-expensive and I will probably curse myself later on for adding this.
             You can always speed it up by building the language IDs and doing one SQL query
            Also attach the test_case_count
        """
        loaded_data = super().data
        loaded_data['supported_languages'] = [Language.objects.get(id=lang_id).name for lang_id in loaded_data['supported_languages']]

        return loaded_data


class HomeworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Homework
        fields = ('is_mandatory',)

    @property
    def data(self):
        """
            Attach the HomeworkTasks
        """
        loaded_data = super().data
        loaded_data['tasks'] = [HomeworkTaskSerializer(hw).data for hw in self.instance.homeworktask_set.all()]

        return loaded_data


class TaskSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = ('task', 'code', 'language', 'author')

    def create(self, validated_data):
        task_submission: TaskSubmission = super().create(validated_data)

        TaskTestCase.objects.bulk_create([TaskTestCase(submission=task_submission) for _ in range(task_submission.task.test_case_count)])

        return task_submission


class TaskTestCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskTestCase
        fields = '__all__'
