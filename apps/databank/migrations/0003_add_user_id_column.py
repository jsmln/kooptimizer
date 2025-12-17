# Add user_id column to replace user ForeignKey

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('databank', '0002_alter_ocrscansession'),
    ]

    operations = [
        # Add user_id as IntegerField with a default value for existing rows
        migrations.AddField(
            model_name='ocrscansession',
            name='user_id',
            field=models.IntegerField(db_index=True, default=1),
            preserve_default=False,
        ),
    ]
