from django.db import connection


def test_procrastinate_schema_is_migrated(db: None) -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT to_regclass('procrastinate_jobs')")
        assert cursor.fetchone() == ("procrastinate_jobs",)
