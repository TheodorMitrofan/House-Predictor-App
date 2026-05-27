from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('predictions', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='prediction',
            name='ai_explanation',
            field=models.TextField(blank=True, db_column='aiExplanation', null=True),
        ),
        migrations.AddField(
            model_name='prediction',
            name='ai_tips_data',
            field=models.JSONField(blank=True, db_column='aiTipsData', null=True),
        ),
    ]
