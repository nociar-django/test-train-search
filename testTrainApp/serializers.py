from django.contrib.auth.models import User, Group
from testTrainApp.models import Train, Station, TrainStop
from rest_framework import serializers

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']

class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']
'''
class TrainSerializer(serializers.Serializer):
    number = serializers.IntegerField(required=True)
    name = serializers.CharField(max_length=128)

    def create(self, validated_data):
        return Train.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.number = validated_data.get('number', instance.number)
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
'''
class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = ['number', 'name']

