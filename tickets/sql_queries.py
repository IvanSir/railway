from django.db import connection

def insert_query(table_name, fields, values):

    values = ', '.join([f"'{value}'" for value in values])
    fields = ', '.join(fields)

    query = f'INSERT INTO "{table_name}" ({fields}) VALUES ({values})'
    with connection.cursor() as cursor:
        cursor.execute(query)


def delete_query(table_name, where_clause=None):

    query = f'DELETE FROM "{table_name}"'

    if where_clause:
        wheres = []
        for key, value in where_clause.items():
            if key == 'pk':
                key = 'id'
            wheres.append(f'{key}={value}')

        wheres = ' AND '.join(wheres)
        query += f' WHERE {wheres}'
    with connection.cursor() as cursor:
        cursor.execute(query)


def update_query(table_name, set_fields, where_clause=None):
    fields_values = []
    for key, value in set_fields.items():
        fields_values.append(f"{key}='{value}'")

    query = f'UPDATE {table_name} SET {", ".join(fields_values)}'

    if where_clause:
        wheres = []
        for key, value in where_clause.items():
            if key == 'pk':
                key = 'id'
            wheres.append(f'{key}={value}')

        wheres = ' AND '.join(wheres)
        query += f' WHERE {wheres}'
    with connection.cursor() as cursor:
        cursor.execute(query)


def select_query(table_name, fields='*', where_clause=None):
    if fields != '*':
        fields = ', '.join([f'"{value}"' for value in fields])

    query = f'SELECT {fields} FROM "{table_name}"'

    if where_clause:
        wheres = []
        for key, value in where_clause.items():
            if key == 'pk':
                key = 'id'
            wheres.append(f"{key}='{value}'")

        wheres = ' AND '.join(wheres)
        query += f' WHERE {wheres}'
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    return rows



def custom_query(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
    return rows
