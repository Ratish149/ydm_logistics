from rest_framework import serializers


class FranchiseStatementSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_order = serializers.IntegerField()
    total_amount = serializers.FloatField()
    delivery_count = serializers.IntegerField()
    cash_in = serializers.FloatField()
    delivery_charge = serializers.FloatField()
    payment = serializers.FloatField()
    balance = serializers.FloatField()
