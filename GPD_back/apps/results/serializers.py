"""
Results — Serializers

API response shape for one submission:
{
  "submission_id": 5,
  "status": "completed",
  "document_results": [
    {
      "document_id":   1,
      "document_name": "thesis.pdf",
      "plagiarism_score":    23.5,
      "original_percentage": 76.5,
      "matched_sources": [          ← sorted most suspicious first
        { "source": "paper1.pdf", "match": 15.0, "color": "#ef4444" },
        { "source": "paper2.pdf", "match":  8.5, "color": "#f97316" }
      ],
      "highlighted_segments": [
        { "text": "...", "highlight": true,  "source": "paper1.pdf" },
        { "text": "...", "highlight": false }
      ]
    },
    ...
  ]
}
"""
from rest_framework import serializers
from .models import DocumentResult, MatchedSource


class MatchedSourceSerializer(serializers.ModelSerializer):
    source = serializers.SerializerMethodField()
    match  = serializers.FloatField(source='match_percentage')
    color  = serializers.SerializerMethodField()

    class Meta:
        model  = MatchedSource
        fields = ['source', 'match', 'color']

    def get_source(self, obj):
        return obj.source.name if obj.source else 'Unknown source'

    def get_color(self, obj):
        return obj.get_color()


class DocumentResultSerializer(serializers.ModelSerializer):
    """One document's complete result — what the frontend shows per-doc."""
    document_id      = serializers.IntegerField(source='document.id')
    document_name    = serializers.CharField(source='document.name')
    matched_sources  = MatchedSourceSerializer(many=True, read_only=True)
    highlighted_segments = serializers.SerializerMethodField()

    class Meta:
        model  = DocumentResult
        fields = [
            'id',
            'document_id',
            'document_name',
            'plagiarism_score',
            'original_percentage',
            'matched_sources',       # sorted by match % desc (model Meta)
            'highlighted_segments',
            'created_at',
        ]

    def get_highlighted_segments(self, obj):
        if obj.segments_json:
            return obj.segments_json
        if obj.highlighted_text:
            return [{'text': obj.highlighted_text, 'highlight': False}]
        return [{'text': 'Analysis complete. See matched sources above.', 'highlight': False}]


class SubmissionResultSerializer(serializers.Serializer):
    """
    Full result for one submission — wraps all document results.
    This is what GET /api/workspaces/{id}/results/ returns.
    """
    submission_id    = serializers.IntegerField()
    status           = serializers.CharField()
    document_results = DocumentResultSerializer(many=True)
