from logging import log
from os import getenv
from dotenv import load_dotenv
import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    Float,
    Date,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    ForeignKey,
)
from sqlalchemy.engine import ExceptionContext
from sqlalchemy.orm import sessionmaker, declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = "user_info"

    userid = Column(Integer, primary_key=True)
    balance = Column(Float, default=0.0)
    datejoined = Column(Date, default=datetime.date.today())


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True)
    userid = Column(Integer, ForeignKey("user_info.userid"))
    transaction_detail = Column(Text)
    transaction_date = Column(TIMESTAMP, default=datetime.datetime.now())
    amount_credited = Column(Float)


class Service(Base):
    __tablename__ = "services"

    service_id = Column(Integer, primary_key=True)
    service_name = Column(Text, unique=True)
    price = Column(Float)
    service_code = Column(Text, unique=True)


class UserDatabase:
    def __init__(self, connection_string):
        self.engine = create_engine(connection_string)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_user(self, userid):
        with self.Session() as session:
            new_user = User(userid=userid)
            session.add(new_user)
            session.commit()

    def get_user_transactions(self, user_id):
        with self.Session() as session:
            return session.query(Transaction).filter_by(userid=user_id).all()

    def check_user_exists(self, user_id):
        with self.Session() as session:
            return session.query(User).filter_by(userid=user_id).exists()

    def get_user_balance(self, user_id):
        with self.Session() as session:
            user = session.query(User).filter_by(userid=user_id).first()
            if not user:
                self.add_user(user_id)
                return 0
            return user.balance

    def recharge_balance(self, user_id, amount):
        with self.Session() as session:
            user = session.query(User).filter_by(userid=user_id).first()
            user.balance += amount
            session.commit()

    def record_order(self, user_id, prod_detail, amount):
        with self.Session() as session:
            transaction = Transaction(
                userid=user_id, transaction_detail=prod_detail, amount_credited=-amount
            )
            session.add(transaction)
            user = session.query(User).filter_by(userid=user_id).first()
            user.balance -= amount
            session.commit()

    def record_transaction(self, user_id, transaction_detail, amount_credited):
        with self.Session() as session:
            transaction = Transaction(
                userid=user_id,
                transaction_detail=transaction_detail,
                amount_credited=amount_credited,
            )
            session.add(transaction)
            user = session.query(User).filter_by(userid=user_id).first()
            user.balance += amount_credited
            session.commit()

    def add_service(self, service_name, price, service_code):
        with self.Session() as session:
            new_service = Service(
                service_name=service_name, price=price, service_code=service_code
            )
            session.add(new_service)
            session.commit()

    def get_service_by_code(self, service_code):
        with self.Session() as session:
            return session.query(Service).filter_by(service_code=service_code).first()


class api_point:
    def __init__(self) -> None:
        try:
            if __name__ == "__main__":
                postgreurl = input("Enter the URL for the Datbase")
            else:
                postgreurl = getenv("POSTGRESQL_DB")
        except BaseException as e:
            log(1, "Error Connecting with database")
            raise e
        finally:
            self.user_db = UserDatabase(postgreurl)

    def see_balance(self, user_id) -> float:
        return float(self.user_db.get_user_balance(user_id))

    def add_balance(self, user_id, amount) -> bool:
        try:
            self.user_db.recharge_balance(user_id, amount)
            return True
        except Exception:
            log(2, f"Unable to recharge {user_id} in the Database")
            return False

    def add_transactions(self, user_id, transaction_detail, amount_credited):
        try:
            self.user_db.record_transaction(
                user_id, transaction_detail, amount_credited
            )
            return True
        except:
            log(
                2, f"Unable to record txns {user_id,transaction_detail,amount_credited}"
            )
            return False

    def see_transactions(self, user_id):
        try:
            x = self.user_db.get_user_transactions(user_id)
            return "\n".join(
                "{:<4} {:<10}".format(i.amount_credited, i.transaction_detail)
                for i in x
            )
        except Exception as e:
            log(2, f"Error while fetching transactions for {user_id}")


def test_debasish():
    myid = 890642031
    reception_1 = api_point()

    # Check Recharge
    old_bal = reception_1.see_balance(myid)
    reception_1.add_balance(user_id=myid, amount=10)
    new_bal = reception_1.see_balance(myid)
    assert old_bal + 10 == new_bal

    # Check Transactions
    reception_1.add_transactions(myid, "A Test Transaction", -12)
    new_bal = reception_1.see_balance(myid)
    assert new_bal == old_bal - 2
    print(reception_1.see_transactions(myid))

reception_api = api_point()

if __name__=='__main__':
    test_debasish()


