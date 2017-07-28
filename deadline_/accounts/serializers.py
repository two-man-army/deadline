from rest_framework import serializers
from accounts.models import User, Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'score', 'role')

    @property
    def data(self):
        data_returned = super().data
        del data_returned['password']
        role_id = data_returned['role']
        del data_returned['role']
        role = Role.objects.get(id=role_id)
        data_returned['role'] = {'id': role_id, 'name': role.name}
        return data_returned
