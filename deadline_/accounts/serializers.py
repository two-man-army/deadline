import re
from collections import OrderedDict

from rest_framework import serializers
from accounts.models import User, Role, UserPersonalDetails
from accounts.constants import (FACEBOOK_PROFILE_REGEX, GITHUB_PROFILE_REGEX,
                                LINKEDIN_PROFILE_REGEX, TWITTER_PROFILE_REGEX)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'score', 'role')

    def to_representation(self, instance):
        data_returned = dict(super().to_representation(instance))
        del data_returned['password']
        role_id = data_returned['role']
        del data_returned['role']
        role = Role.objects.get(id=role_id)
        data_returned['role'] = {'id': role_id, 'name': role.name}
        return OrderedDict(data_returned)


class UserPersonalDetailsSerializer(serializers.ModelSerializer):
    facebook_profile = serializers.CharField()
    twitter_profile = serializers.CharField()
    github_profile = serializers.CharField()
    linkedin_profile = serializers.CharField()

    class Meta:
        model = UserPersonalDetails
        fields = ('about', 'country', 'city', 'school', 'school_major', 'job_title',
                  'job_company', 'personal_website', 'interests', 'facebook_profile',
                  'twitter_profile', 'github_profile', 'linkedin_profile')

    def validate_facebook_profile(self, value):
        match_data = re.match(pattern=FACEBOOK_PROFILE_REGEX, string=value)

        if match_data is None:
            raise serializers.ValidationError('Invalid Facebook profile URL')

        return match_data.group('page_name')

    def validate_twitter_profile(self, value):
        match_data = re.match(pattern=TWITTER_PROFILE_REGEX, string=value)

        if match_data is None:
            raise serializers.ValidationError('Invalid Twitter profile URL')

        return match_data.group('profile_name')

    def validate_github_profile(self, value):
        match_data = re.match(pattern=GITHUB_PROFILE_REGEX, string=value)

        if match_data is None:
            raise serializers.ValidationError('Invalid GitHub profile URL')

        return match_data.group('profile_name')

    def validate_linkedin_profile(self, value):
        match_data = re.match(pattern=LINKEDIN_PROFILE_REGEX, string=value)

        if match_data is None:
            raise serializers.ValidationError('Invalid LinekdIn profile URL')

        return match_data.group('profile_name')
