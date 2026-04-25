from django.db import migrations, connection


def drop_token_blacklist_constraints(apps, schema_editor):
    """
    SQL Server auto-generates unique constraints that block
    column type changes. Drop them before simplejwt 0008
    tries to alter token_id to BigAutoField.
    Only executes on SQL Server — safe no-op on SQLite/PostgreSQL.
    """
    if connection.vendor != 'microsoft':
        return

    with connection.cursor() as cursor:
        cursor.execute("""
            USE tempdb;
            DECLARE @sql NVARCHAR(MAX) = '';
            SELECT @sql = @sql +
                'ALTER TABLE [token_blacklist_outstandingtoken]
                 DROP CONSTRAINT [' + name + '];'
            FROM sys.objects
            WHERE type = 'UQ'
              AND parent_object_id =
                  OBJECT_ID('token_blacklist_outstandingtoken');
            IF LEN(@sql) > 0
                EXEC sp_executesql @sql;
        """)


class Migration(migrations.Migration):

    dependencies = [
        # Your previous accounts migration
        ("accounts", "0001_initial"),
        # Must run AFTER 0007, BEFORE 0008
        ("token_blacklist", "0007_auto_20171017_2214"),
    ]

    operations = [
        migrations.RunPython(
            drop_token_blacklist_constraints,
            reverse_code=migrations.RunPython.noop,
        ),
    ]