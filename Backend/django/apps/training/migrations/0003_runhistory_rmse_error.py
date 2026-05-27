from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0002_fix_training_data_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='runhistory',
            name='rmse',
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='runhistory',
            name='error_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
