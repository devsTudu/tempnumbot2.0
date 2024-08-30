import os
import psycopg2
from dotenv import load_dotenv
import sqlite3
load_dotenv()

class UserDatabase:
    def __init__(self, connection: psycopg2.connect):
        self.conn = connection
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("SET SESSION TIME ZONE 'Asia/Kolkata';")
        cursor.execute('''CREATE TABLE IF NOT EXISTS user_info (
                          userid INTEGER PRIMARY KEY,
                          balance REAL DEFAULT 0.0,
                          datejoined DATE DEFAULT CURRENT_TIMESTAMP
                      )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                          transaction_id SERIAL PRIMARY KEY,
                          userid INTEGER,
                          transaction_detail TEXT,
                          transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          amount_credited REAL
                      )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS services (
                          service_id SERIAL PRIMARY KEY,
                          service_name TEXT UNIQUE,
                          price REAL,
                          service_code TEXT UNIQUE
                      )''')
        self.conn.commit()

    def add_user(self, userid):  # Consider adding username as a parameter
        cursor = self.conn.cursor()
        cursor.execute(f'''INSERT INTO user_info (userid) VALUES ({userid})''')
        self.conn.commit()

    def get_user_transactions(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            f'''SELECT * FROM transactions WHERE userid = {user_id}''')
        return cursor.fetchall()

    def check_user_exists(self, user_id):
        """
        Checks if a user ID already exists in the user_info table.

        Args:
            user_id (int): The user ID to check.

        Returns:
            bool: True if the user ID exists, False otherwise.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
        SELECT EXISTS(
          SELECT 1
          FROM user_info
          WHERE userid = %s
        );
      """, (user_id,))

            # Get the first element from the returned tuple
            exists = cursor.fetchone()[0]
            return exists
        except (Exception, psycopg2.Error) as error:
            print("Error checking user existence:", error)
            return False
        finally:
            cursor.close()

    def get_user_balance(self, user_id):
        cursor = self.conn.cursor()
        if self.check_user_exists(user_id):
            cursor.execute('''SELECT balance FROM user_info WHERE userid = %s''',
                           (user_id, ))
            return cursor.fetchone()[0]  # Assuming only one row is returned
        else:
            self.add_user(user_id)
            return 0

    def recharge_balance(self, user_id, amount):
        self.record_transaction(user_id, "Main Recharge", amount)

    def record_order(self, user_id, prod_detail, amount):
        self.record_transaction(user_id, f"{prod_detail}", -int(amount))

    def record_transaction(self, user_id, transaction_detail, amount_credited):
        amount_credited = float(amount_credited)
        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT INTO transactions (userid, transaction_detail,
        amount_credited) VALUES (%s, %s, %s)''',
            (user_id, transaction_detail, amount_credited))
        cursor.execute('''UPDATE user_info SET balance = balance + %s WHERE
    userid = %s''', (amount_credited, user_id))
        self.conn.commit()

    def add_service(self, service_name, price, service_code):
        cursor = self.conn.cursor()
        cursor.execute(
            '''INSERT INTO services (service_name, price, service_code) VALUES (?, ?, ?)''',
            (service_name, price, service_code))
        self.conn.commit()

    def get_service_by_code(self, service_code):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT * FROM services WHERE service_code = ?''',
                       (service_code, ))
        return cursor.fetchone()



class UserDatabase_lite:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = sqlite3.connect(db_file)
        self.cur = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cur.execute('''CREATE TABLE IF NOT EXISTS user_info (
            userid INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            datejoined DATETIME DEFAULT CURRENT_TIMESTAMP
        )''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            userid INTEGER,
            transaction_detail TEXT,
            transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            amount_credited REAL
        )''')
        self.cur.execute('''CREATE TABLE IF NOT EXISTS services (
            service_id INTEGER PRIMARY KEY AUTOINCREMENT,
            service_name TEXT UNIQUE,
            price REAL,
            service_code TEXT UNIQUE
        )''')
        self.conn.commit()

    def add_user(self, userid):
        cursor = self.cur
        cursor.execute("INSERT INTO user_info (userid) VALUES (?)", (userid,))
        self.conn.commit()

    def get_user_transactions(self, user_id):
        cursor = self.cur
        cursor.execute("SELECT * FROM transactions WHERE userid = ?", (user_id,))
        return cursor.fetchall()

    def check_user_exists(self, user_id):
        cursor = self.cur
        try:
            cursor.execute("SELECT EXISTS(SELECT 1 FROM user_info WHERE userid = ?)", (user_id,))
            exists = cursor.fetchone()[0]
            return exists
        except sqlite3.Error as error:
            print("Error checking user existence:", error)
            return False
        finally:
            cursor.close()

    def get_user_balance(self, user_id):
        cursor = self.cur
        if self.check_user_exists(user_id):
            cursor.execute("SELECT balance FROM user_info WHERE userid = ?", (user_id,))
            return cursor.fetchone()[0]
        else:
            self.add_user(user_id)
            return 0

    def recharge_balance(self, user_id, amount):
        self.record_transaction(user_id, "Main Recharge", amount)

    def record_order(self, user_id, prod_detail, amount):
        self.record_transaction(user_id, f"{prod_detail}", -int(amount))

    def record_transaction(self, user_id, transaction_detail, amount_credited):
        cursor = self.cur
        cursor.execute("INSERT INTO transactions (userid, transaction_detail, amount_credited) VALUES (?, ?, ?)",
                       (user_id, transaction_detail, float(amount_credited)))
        cursor.execute("UPDATE user_info SET balance = balance + ? WHERE userid = ?",
                       (float(amount_credited), user_id))
        self.conn.commit()

    def add_service(self, service_name, price, service_code):
        cursor = self.cur
        cursor.execute("INSERT INTO services (service_name, price, service_code) VALUES (?, ?, ?)",
                       (service_name, price, service_code))
        self.conn.commit()

    def get_service_by_code(self, service_code):
        cursor = self.cur
        cursor.execute("SELECT * FROM services WHERE service_code = ?", (service_code,))
        return cursor.fetchone()

    def close(self):
        self.conn.close()
 

class test:
    def __init__(self, connection, user_db) -> None:
        self.conn = connection
        self.user_db = user_db

    def recharge(self):
        user_id = int(input("Enter the user Id to see balance:"))
        print(self.user_db.get_user_balance(
            user_id), "is there current balance")
        recharge = int(input("Amount to recharge :"))
        self.user_db.recharge_balance(user_id, recharge)
        print(user_db.get_user_balance(user_id), "is there current balance")

    def transaction(self):
        userid = input("Enter the userid:")
        trans = input("Input Traxn detail:")
        amount = int(input("Enter the amount credited:"))
        self.user_db.record_transaction(
            user_id=userid,
            transaction_detail=trans,
            amount_credited=amount)

if os.getenv('USE_LITE_DB') == "YES":
    user_db = UserDatabase_lite('user.db')
else:
    try:
        conn = psycopg2.connect(os.getenv('POSTGRESQL_DB'))
        user_db = UserDatabase(conn)
    except psycopg2.OperationalError as e:
        print(os.getenv('POSTGRESQL_DB'))
        raise e
    except Exception as e:
        raise e


myid = 890642031
    

if __name__ == '__main__':
    id = myid  # input()
    
    print(user_db.get_user_balance(myid), 'is your balance')
    user_db.recharge_balance(myid,23)
    print('Recharged 23')
    x = (user_db.get_user_transactions(id))
    print(user_db.get_user_balance(myid), 'is your balance')
    y = "\n".join("{:<4} {:<10}".format(i[-1], i[2]) for i in x)
    print(y)
