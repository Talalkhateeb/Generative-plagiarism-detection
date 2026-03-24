from rest_framework import serializers
from .models import Plan


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Plan
        fields = [
            'id', 'name', 'price', 'checks_per_month',
            'max_sources', 'max_documents', 'allowed_formats', 'is_active',
        ]


class PlanCreateUpdateSerializer(serializers.ModelSerializer):
    """Admin: create or update a plan (UC-8)."""
    class Meta:
        model  = Plan
        fields = [
            'name', 'price', 'checks_per_month',
            'max_sources', 'max_documents', 'allowed_formats', 'is_active',
        ]
