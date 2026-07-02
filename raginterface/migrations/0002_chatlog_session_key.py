from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('raginterface', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatlog',
            name='session_key',
            field=models.CharField(blank=True, max_length=40, null=True, unique=True),
        ),
    ]