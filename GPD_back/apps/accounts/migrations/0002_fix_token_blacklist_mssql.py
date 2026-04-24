from django.db import migrations


class Migration(migrations.Migration):
    """
    Fix for mssql-django bug: token_blacklist.0008 tries to alter 'token_id'
    column but SQL Server blocks it due to a dependent unique constraint.
    We drop the constraint before the migration and recreate it after.
    """

    dependencies = [
        ('accounts', '0001_initial'),
        ('token_blacklist', '0007_auto_20171017_2214'),
    ]

    operations = [
        migrations.RunSQL(
            # Drop the auto-generated unique constraint before migration 0008 runs
            sql="""
                DECLARE @sql NVARCHAR(MAX) = '';
                SELECT @sql = @sql + 
                    'ALTER TABLE [token_blacklist_outstandingtoken] DROP CONSTRAINT [' + name + '];'
                FROM sys.objects
                WHERE type = 'UQ'
                  AND parent_object_id = OBJECT_ID('token_blacklist_outstandingtoken')
                  AND name LIKE 'UQ__token_bl__%';
                EXEC sp_executesql @sql;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]