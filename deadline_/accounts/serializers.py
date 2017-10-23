from collections import OrderedDict

from rest_framework import serializers

from accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'score', 'role')

    def to_representation(self, instance):
        repr = dict(super().to_representation(instance))

        del repr['password']
        repr['role'] = {'id': self.instance.role.id, 'name': self.instance.role.name}

        return OrderedDict(repr)
