import psycopg2


# создания БД
def create_db(conn):
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            first_name VARCHAR(50) NOT NULL,
            last_name VARCHAR(50) NOT NULL,
            email VARCHAR(50) NOT NULL UNIQUE
        )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS phones (
            id SERIAL PRIMARY KEY,
            client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
            phone VARCHAR(15)
        )
        """
        )
    conn.commit()


# добавления клиента
def add_client(conn, first_name, last_name, email, phones=None):
    with conn.cursor() as cur:
        cur.execute(
            """
                        INSERT INTO clients (first_name, last_name, email)
                        VALUES (%s, %s, %s) RETURNING id""",
            (first_name, last_name, email),
        )
        client_id = cur.fetchone()[0]

        if phones:
            for phone in phones:
                add_phone(conn, client_id, phone)

    conn.commit()


# добавления телефона для клиента
def add_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute(
            """
        INSERT INTO phones (client_id, phone) VALUES (%s, %s)""",
            (client_id, phone),
        )
    conn.commit()


# изменения данных о клиенте
def change_client(conn, client_id, first_name=None, last_name=None, email=None, phones=None):
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM clients WHERE id = %s", (client_id,))
        if cur.fetchone()[0] == 0:
            raise ValueError("Клиент с ID не найден")

        if first_name:
            cur.execute(
                """
            UPDATE clients SET first_name = %s WHERE id = %s
            """,
                (first_name, client_id),
            )
        if last_name:
            cur.execute(
                """
            UPDATE clients SET last_name = %s WHERE id = %s
            """,
                (last_name, client_id),
            )
        if email:
            cur.execute(
                """
            UPDATE clients SET email = %s WHERE id = %s
            """,
                (email, client_id),
            )
        if phones:
            cur.execute(
                """
            DELETE FROM phones WHERE client_id = %s
            """,
                (client_id,),
            )
            for phone in phones:
                add_phone(conn, client_id, phone)
    conn.commit()


# удаления телефона клиента
def delete_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute(
            """
        DELETE FROM phones WHERE client_id = %s AND phone = %s
        """,
            (client_id, phone),
        )
    conn.commit()


# удаления клиента
def delete_client(conn, client_id):
    with conn.cursor() as cur:
        cur.execute(
            """
        DELETE FROM clients WHERE id = %s
        """,
            (client_id,),
        )
    conn.commit()


# поиск клиента по данным
def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    with conn.cursor() as cur:
        query = "SELECT * FROM clients WHERE "
        conditions = []
        parameters = []

        if first_name:
            conditions.append("first_name = %s")
            parameters.append(first_name)
        if last_name:
            conditions.append("last_name = %s")
            parameters.append(last_name)
        if email:
            conditions.append("email = %s")
            parameters.append(email)
        if phone:
            conditions.append("id IN (SELECT client_id FROM phones WHERE phone = %s)")
            parameters.append(phone)

        if conditions:
            query += " AND ".join(conditions)
        else:
            return []

        cur.execute(query, parameters)
        result = cur.fetchall()
        return result


# удаление клиента
def drop_tables(conn):
    with conn.cursor() as cur:
        # Удаляем таблицы, если они существуют
        cur.execute("DROP TABLE IF EXISTS phones CASCADE")
        cur.execute("DROP TABLE IF EXISTS clients CASCADE")

    conn.commit()


if __name__ == "__main__":
    with psycopg2.connect(database="clients_db", user="postgres", password="123") as conn:

        # создание базы данных и таблиц
        print("Создание базы данных и таблиц...")
        create_db(conn)

        # добавление клиентов
        print("\nДобавление клиентов...")
        add_client(conn, "Иван", "Иванов", "ivan@example.com", ["+79001234567", "+79007654321"])
        add_client(conn, "Петр", "Петров", "petr@example.com", ["+79009876543"])
        add_client(conn, "Светлана", "Сидорова", "svetlana@example.com", ["+79001122334"])

        # поиск клиентов
        print("\nПоиск клиента по имени 'Иван':", find_client(conn, first_name="Иван"))
        print("Поиск клиента по фамилии 'Петров':", find_client(conn, last_name="Петров"))
        print("Поиск клиента по email 'svetlana@example.com':", find_client(conn, email="svetlana@example.com"))
        print("Поиск клиента по телефону '+79001234567':", find_client(conn, phone="+79001234567"))

        # изменение данных клиента
        print("\nИзменение данных клиента с ID 1 (Иван Иванов):")
        change_client(
            conn,
            1,
            first_name="Иван",
            last_name="Иванов",
            email="ivanov@example.com",
            phones=["+79001234567", "+79005554433"],
        )
        print("Поиск после изменения email и телефонов клиента с ID 1:", find_client(conn, first_name="Иван"))

        # удаление телефона клиента
        print("\nУдаление телефона '+79005554433' у клиента с ID 1:")
        delete_phone(conn, 1, "+79005554433")
        print("Поиск после удаления телефона у клиента с ID 1:", find_client(conn, first_name="Иван"))

        # удаление клиента
        print("\nУдаление клиента с ID 2 (Петр Петров):")
        delete_client(conn, 2)
        print("Поиск после удаления клиента с ID 2:", find_client(conn, first_name="Петр"))

        # удаление таблиц
        print("\nУдаление таблиц...")
        drop_tables(conn)
