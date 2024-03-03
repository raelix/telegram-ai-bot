import json
import sqlite3
from typing import Tuple, Iterator
from typing import Sequence, List, Optional
from langchain.schema import BaseStore
from pypika import Query, Table, Field, Column


class ChromaStore(BaseStore[str, bytes]):

    def __init__(self, path, user_id):
        self.path = path
        self.table_name = "docstore_{}".format(user_id)
        self.table = Table(self.table_name)
        self.id_column = Field('id')
        self.data_column = Field('data')
        self._create_table()

    def get_connection(self):
        return sqlite3.connect('{path}/chroma.sqlite3'.format(path=self.path))

    def _create_table(self):
        id_column = Column('id', 'VARCHAR(50)', nullable=False)
        data_column = Column('data', 'VARCHAR(2500)', nullable=False)
        create_table_query = Query.create_table(self.table).columns(id_column, data_column).if_not_exists()
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(create_table_query.get_sql())
            cursor.close()

    def mget(self, keys: Sequence[str]) -> List[Optional[bytes]]:
        select_query = Query.from_(self.table).select(self.data_column).where(self.id_column.isin(keys))
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(select_query.get_sql())
            results = cursor.fetchall()

            cursor.close()

            data_list = []
            for result in results:
                if result[0] is not None:
                    data_list.append(json.loads(result[0]).encode("utf-8"))
                else:
                    data_list.append(None)

            return data_list

    def mset(self, key_value_pairs: Sequence[Tuple[int, bytes]]) -> None:
        insert_queries = []
        for key, value in key_value_pairs:
            insert_query = Query.into(self.table).columns(self.id_column, self.data_column).insert(key, json.dumps(
                value.decode('utf-8')))
            insert_queries.append(insert_query)
        with self.get_connection() as connection:
            cursor = connection.cursor()
            for query in insert_queries:
                cursor.execute(query.get_sql())
            connection.commit()
            cursor.close()

    def mdelete(self, keys: Sequence[int]) -> None:
        delete_query = Query.from_(self.table).delete().where(self.id_column.isin(keys))
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(delete_query.get_sql())
            connection.commit()
            cursor.close()

    def yield_keys(self, prefix: Optional[str] = None) -> Iterator[str]:
        select_query = Query.from_(self.table).select(self.id_column)
        if prefix:
            select_query = select_query.where(self.id_column.like(f'{prefix}%'))
        with self.get_connection() as connection:
            cursor = connection.cursor()
            cursor.execute(select_query.get_sql())

            for row in cursor.fetchall():
                yield row[0]

            cursor.close()
