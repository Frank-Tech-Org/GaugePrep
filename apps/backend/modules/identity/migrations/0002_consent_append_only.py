from config.append_only import append_only
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("identity", "0001_initial")]

    operations = [append_only("identity.consent")]
