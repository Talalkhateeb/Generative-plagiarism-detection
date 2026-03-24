"""
Migration: replace single Result model with per-document DocumentResult.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('results',      '0001_initial'),
        ('workspaces',   '0001_initial'),
        ('submissions',  '0001_initial'),
    ]

    operations = [
        # Drop old single-result models
        migrations.DeleteModel(name='MatchedSource'),
        migrations.DeleteModel(name='Result'),

        # Create DocumentResult — one per document per submission
        migrations.CreateModel(
            name='DocumentResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plagiarism_score',    models.FloatField(default=0.0)),
                ('original_percentage', models.FloatField(default=100.0)),
                ('highlighted_text',    models.TextField(blank=True)),
                ('segments_json',       models.JSONField(default=list)),
                ('created_at',          models.DateTimeField(auto_now_add=True)),
                ('submission', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='document_results',
                    to='submissions.submission',
                )),
                ('workspace', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='results',
                    to='workspaces.workspace',
                )),
                ('document', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='results',
                    to='workspaces.document',
                )),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='documentresult',
            constraint=models.UniqueConstraint(
                fields=['submission', 'document'],
                name='unique_result_per_doc_per_submission'
            ),
        ),

        # Create MatchedSource — one per (DocumentResult, Source) pair
        migrations.CreateModel(
            name='MatchedSource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('match_percentage', models.FloatField(default=0.0)),
                ('result', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='matched_sources',
                    to='results.documentresult',
                )),
                ('source', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='workspaces.source',
                )),
            ],
            options={
                'ordering': ['-match_percentage'],
            },
        ),
    ]
