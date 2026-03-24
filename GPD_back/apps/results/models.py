"""
Results App — Models

Each Document in a submission gets its OWN Result.
Structure:
  Submission
    └── DocumentResult  (one per document)
          ├── document         → which doc was checked
          ├── plagiarism_score → e.g. 23.5%
          ├── original_percentage → 76.5%
          └── MatchedSource[]  → sorted by match % descending
                ├── source1.pdf → 15%
                └── source2.pdf →  8%
"""
from django.db import models


class DocumentResult(models.Model):
    """
    One result per document per submission.
    Class Diagram: result(-id, -w_id, -plagiarism_score, -source retrieved_sources[])
    """
    submission          = models.ForeignKey(
        'submissions.Submission', on_delete=models.CASCADE, related_name='document_results'
    )
    workspace           = models.ForeignKey(
        'workspaces.Workspace', on_delete=models.CASCADE, related_name='results'
    )
    document            = models.ForeignKey(
        'workspaces.Document', on_delete=models.CASCADE, related_name='results'
    )
    plagiarism_score    = models.FloatField(default=0.0,
                          help_text='0-100 — percentage of plagiarised content')
    original_percentage = models.FloatField(default=100.0)
    highlighted_text    = models.TextField(blank=True,
                          help_text='Raw text passages flagged as plagiarised')
    segments_json       = models.JSONField(default=list,
                          help_text='[{text, highlight, source?}] for frontend highlighting')
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        # One result per document per submission
        unique_together = [('submission', 'document')]

    def __str__(self):
        return (f'Result: {self.document.name} '
                f'— {self.plagiarism_score:.1f}% plagiarism')

    # Class Diagram: +generate_trec_file(score, sources)
    def generate_trec_file(self):
        lines = [
            f'DOCUMENT: {self.document.name}',
            f'SCORE: {self.plagiarism_score}',
        ]
        for ms in self.matched_sources.all():
            lines.append(f'SOURCE: {ms.source.name}  MATCH: {ms.match_percentage}%')
        return '\n'.join(lines)

    # Class Diagram: +export_pdf_report()
    def export_pdf_report(self):
        return {
            'document':           self.document.name,
            'plagiarism_score':   self.plagiarism_score,
            'original_percentage': self.original_percentage,
            'matched_sources': [
                {
                    'source': ms.source.name if ms.source else 'Unknown',
                    'match':  ms.match_percentage,
                    'color':  ms.get_color(),
                }
                for ms in self.matched_sources.select_related('source').all()
            ],
            'highlighted_segments': self.segments_json or [
                {'text': self.highlighted_text or 'No highlighted text available.', 'highlight': False}
            ],
        }


class MatchedSource(models.Model):
    """
    One row per (document_result, source) pair.
    Sorted by match_percentage descending — most suspicious first.
    """
    result           = models.ForeignKey(
        DocumentResult, on_delete=models.CASCADE, related_name='matched_sources'
    )
    source           = models.ForeignKey(
        'workspaces.Source', on_delete=models.SET_NULL, null=True
    )
    match_percentage = models.FloatField(default=0.0)

    class Meta:
        ordering = ['-match_percentage']   # most suspicious first

    def __str__(self):
        src = self.source.name if self.source else 'Unknown'
        return f'{src}: {self.match_percentage}%'

    def get_color(self):
        if self.match_percentage >= 20:
            return '#ef4444'   # red   — high risk
        elif self.match_percentage >= 10:
            return '#f97316'   # orange — medium
        elif self.match_percentage >= 5:
            return '#eab308'   # yellow — low
        else:
            return '#22c55e'   # green  — negligible
