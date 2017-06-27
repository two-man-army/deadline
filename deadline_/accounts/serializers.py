from rest_framework import serializers
from accounts.models import User, Role


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'score', 'role')

    @property
    def data(self):
        """
        Attach the Role's name
        """
        loaded_data = super().data
        loaded_data['role'] = Role.objects.get(id=loaded_data['role']).name
        return loaded_data
