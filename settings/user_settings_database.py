import sqlite3
from pypika import Query, Table, Field, Column, SQLLiteQuery


class UserSettingsDatabase:
    _db_file_name: str = "settings.sqlite3"
    db_path: str = "./production_database"

    def __init__(self, user_id):
        self.user_id = user_id
        self.tables = dict(
            features=dict(
                name=Table("features_{}".format(user_id)),
                columns=[Column('name', 'VARCHAR(50)', nullable=False),
                         Column('is_enabled', 'INTEGER', nullable=False)],
                unique="name",
                fields=dict(
                    name=Field('name'),
                    is_enabled=Field('is_enabled')
                ),
            ),
            settings=dict(
                name=Table("settings_{}".format(user_id)),
                columns=[Column('key', 'VARCHAR(50)', nullable=False),
                         Column('value', 'VARCHAR(2500)', nullable=False)],
                unique="key",
                fields=dict(
                    key=Field('key'),
                    value=Field('value')
                ),
            ),
        )
        self._create_tables()

    def get_connection(self):
        return sqlite3.connect('{path}/{db_file_name}'.format(
            path=self.db_path,
            db_file_name=self._db_file_name)
        )

    def _create_tables(self):
        for _, table_object in self.tables.items():
            stmt = (Query.create_table(table_object["name"])
                    .columns(*table_object["columns"])
                    .unique(table_object["unique"])
                    .if_not_exists())
            print("SQL executed: {}".format(stmt))
            self._execute_query(stmt)

    def _execute_query(self, query):
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(query.get_sql())
            result = cursor.fetchall()
            cursor.close()
        return result

    def is_enabled_feature(self, feature_name: str) -> bool:
        table = self.tables["features"]["name"]
        fields = self.tables["features"]["fields"]
        query = (SQLLiteQuery.from_(table)
                 .select(fields["is_enabled"])
                 .where(fields["name"].eq(feature_name)))
        result = self._execute_query(query)
        return result[0][0] == 1 if result else False

    def set_feature(self, feature_name: str, is_enabled: bool) -> None:
        val = 0
        if is_enabled:
            val = 1
        table = self.tables["features"]["name"]
        insert_query = (SQLLiteQuery.into(table)
                        .insert_or_replace(feature_name, val))
        self._execute_query(insert_query)

    def get_setting(self, key: str) -> str:
        table = self.tables["settings"]["name"]
        fields = self.tables["settings"]["fields"]
        query = (SQLLiteQuery.from_(table)
                 .select(fields["value"])
                 .where(fields["key"].eq(key)))
        result = self._execute_query(query)
        return result[0][0] if result else None

    def set_setting(self, key: str, value: str) -> None:
        table = self.tables["settings"]["name"]
        insert_query = (SQLLiteQuery.into(table)
                        .insert_or_replace(key, value))
        self._execute_query(insert_query)
