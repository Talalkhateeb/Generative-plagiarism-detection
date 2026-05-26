from django.db import migrations, connection


def drop_token_blacklist_constraints(apps, schema_editor):
    """
    SQL Server blocks altering a column that has a dependent unique
    constraint. This drops ALL unique constraints on the
    token_blacklist_outstandingtoken table before 0008 runs.
    """
    if connection.vendor != 'microsoft':
        return

    with connection.cursor() as cursor:
        # Get the actual database name Django is connected to
        cursor.execute("SELECT DB_NAME()")
        row = cursor.fetchone()
        db_name = row[0] if row else 'tempdb'

        # Drop all unique constraints on the table using
        # fully qualified name to avoid context issues
        cursor.execute(f"""
            DECLARE @sql NVARCHAR(MAX) = '';
            SELECT @sql = @sql +
                'ALTER TABLE [{db_name}].[dbo].[token_blacklist_outstandingtoken]
                 DROP CONSTRAINT [' + o.name + '];'
            FROM [{db_name}].sys.objects o
            WHERE o.type = 'UQ'
              AND o.parent_object_id =
                  OBJECT_ID('[{db_name}].[dbo].[token_blacklist_outstandingtoken]');
            IF LEN(@sql) > 0
                EXEC sp_executesql @sql;
        """)


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("token_blacklist", "0007_auto_20171017_2214"),
    ]

    operations = [
        migrations.RunPython(
            drop_token_blacklist_constraints,
            reverse_code=migrations.RunPython.noop,
        ),
    ]