# Generated manually to handle user field change

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('databank', '0001_initial'),
    ]

    operations = [
        # The user_id column already exists in the table
        # Just remove the user ForeignKey field if it exists
        migrations.RemoveField(
            model_name='ocrscansession',
            name='user',
        ),
        # Ensure table name is correct
        migrations.AlterModelTable(
            name='ocrscansession',
            table='databank_ocrscansession',
        ),
    ]
