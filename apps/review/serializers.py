from rest_framework import serializers


class ReviewRequestSerializer(serializers.Serializer):
    record_type = serializers.ChoiceField(choices=("FUEL", "ELECTRICITY", "TRAVEL"))
    record_id = serializers.IntegerField(min_value=1)

