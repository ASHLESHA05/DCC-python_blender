import sqlite3
from contextlib import contextmanager


class SQLiteDB:
    def __init__(self, db_path):
        """Initialize SQLite database connection."""
        self.db_path = db_path
        self._create_tables()

    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _create_tables(self):
        """Create necessary tables if they don't exist."""
        create_table_query = '''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                quantity INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''

        create_update_log = '''
            CREATE TABLE IF NOT EXISTS item_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                old_quantity INTEGER,
                new_quantity INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''

        create_delete_log = '''
            CREATE TABLE IF NOT EXISTS delete_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_name TEXT,
                quantity INTEGER,
                deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''

        create_trigger_query = '''
            CREATE TRIGGER IF NOT EXISTS after_item_update
            AFTER UPDATE ON items
            FOR EACH ROW
            WHEN OLD.quantity != NEW.quantity
            BEGIN
                INSERT INTO item_log (item_name, old_quantity, new_quantity, updated_at)
                VALUES (OLD.name, OLD.quantity, NEW.quantity, CURRENT_TIMESTAMP);
            END;
        '''

        delete_trigger = '''
            CREATE TRIGGER IF NOT EXISTS after_item_delete
            AFTER DELETE ON items
            FOR EACH ROW
            BEGIN
                INSERT INTO delete_log (item_name, quantity, deleted_at)
                VALUES (OLD.name, OLD.quantity, CURRENT_TIMESTAMP);
            END;
        '''

        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_query)
                cursor.execute(create_update_log)
                cursor.execute(create_delete_log)
                cursor.execute(create_trigger_query)
                cursor.execute(delete_trigger)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error creating tables: {str(e)}")
            raise

    def add_item(self, data):
        """Add a new item to the inventory."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO items (name, quantity) VALUES (?, ?)',
                    (data['name'], data['quantity'])
                )
                conn.commit()
            return 201, "Item successfully added to database"
        except sqlite3.IntegrityError as e:
            return 400, f"Item already exists: {str(e)}"
        except sqlite3.Error as e:
            return 500, f"Database error: {str(e)}"

    def get_all_items(self):
        """Retrieve all items from the inventory."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM items')
                return cursor.fetchall()
        except sqlite3.Error as e:
            return None, f"Database error: {str(e)}"

    def remove_item(self, data):
        """Remove an item from the inventory based on its name."""
        try:
            name = data['name']
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM items WHERE name = ?', (name,))
                conn.commit()
            return 200, "Item deleted successfully"
        except sqlite3.Error as e:
            return 500, f"Database error: {str(e)}"

    def update_qty(self, data):
        """Update the quantity of an existing item."""
        try:
            name, new_qty = data['name'], data['quantity']
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE items SET quantity = ? WHERE name = ?', (new_qty, name))
                conn.commit()
            return 200, "Item quantity updated successfully"
        except sqlite3.Error as e:
            return 500, f"Database error: {str(e)}"

    def get_all_delete_logs(self, data=None):
        """Retrieve delete logs with optional filtering by date range."""
        try:
            _from = data.get('_from') if data else None
            _to = data.get('_to') if data else None

            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                if not _from and not _to:
                    cursor.execute('SELECT * FROM delete_log')
                elif not _from:
                    cursor.execute('SELECT * FROM delete_log WHERE deleted_at <= ?', (_to,))
                elif not _to:
                    cursor.execute('SELECT * FROM delete_log WHERE deleted_at >= ?', (_from,))
                else:
                    cursor.execute('SELECT * FROM delete_log WHERE deleted_at BETWEEN ? AND ?', (_from, _to))

                data_ = cursor.fetchall()
                return 200 if data_ else ("No records found", 404) ,data_
        except sqlite3.Error as e:
            return 500, f"Database error: {str(e)}"

    def get_all_update_logs(self, data=None):
        """Retrieve update logs with optional filtering by date range."""
        try:
            _from = data.get('_from') if data else None
            _to = data.get('_to') if data else None

            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                if not _from and not _to:
                    cursor.execute('SELECT * FROM item_log')
                elif not _from:
                    cursor.execute('SELECT * FROM item_log WHERE updated_at <= ?', (_to,))
                elif not _to:
                    cursor.execute('SELECT * FROM item_log WHERE updated_at >= ?', (_from,))
                else:
                    cursor.execute('SELECT * FROM item_log WHERE updated_at BETWEEN ? AND ?', (_from, _to))

                data_ = cursor.fetchall()
                return  200 if data_ else ("No records found", 404), data_  
        except sqlite3.Error as e:
            return 500, f"Database error: {str(e)}"
