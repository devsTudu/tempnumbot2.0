from logging import log
import datetime
import os

from sqlalchemy import (
    create_engine,
    Column,
    Integer, BigInteger,
    Float,
    Date,
    Text,
    TIMESTAMP,
    ForeignKey,
    func
)

from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError

Base = declarative_base()
today = datetime.datetime.today()


class User(Base):
    __tablename__ = "user_info"

    userid = Column(BigInteger, primary_key=True)
    balance = Column(Float, default=0.0)
    datejoined = Column(Date, default=datetime.date.today())


class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True)
    userid = Column(BigInteger, ForeignKey("user_info.userid"))
    transaction_detail = Column(Text)
    transaction_date = Column(TIMESTAMP, default=datetime.datetime.now())
    amount_credited = Column(Float)

class Recharges(Base):
    __tablename__ = "recharge_list"
    utr_no = Column(Text, primary_key=True)
    amount = Column(Integer)
    userid = Column(BigInteger, ForeignKey("user_info.userid"))


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

    def record_transaction(self, user_id, transaction_detail, amount_credited):
        with self.Session() as session:
            transaction = Transaction(
                userid=user_id,
                transaction_detail=transaction_detail,
                amount_credited=amount_credited,
            )
            session.add(transaction)
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

    def get_most_buyed(self, user_id):
        with self.Session() as session:
            lis = session.query(Transaction.transaction_detail,
                                func.count(Transaction.transaction_detail
                                           ).label('count')
                                ).filter(Transaction.userid == user_id
                                         ).filter(Transaction.amount_credited < 0).group_by(
                Transaction.transaction_detail
                ).order_by(func.count(Transaction.transaction_detail).desc()
                           ).all()

            return [item.transaction_detail for item in lis]

    def add_recharge(self, user_id, amount, utr):
        with self.Session() as session:
            new_recharge = Recharges(userid=user_id, amount=abs(amount), utr_no=str(utr))
            log(1, f'Checking recharge at {utr}')
            try:
                session.add(new_recharge)
                session.commit()
                self.record_transaction(user_id, 'Recharge', abs(amount))
                return True
            except IntegrityError as i:
                return False
            except Exception as e:
                log(2, "Recharge Recording Issue")
                raise e

    def get_new_members_joined(self, only_today=False):
        """
        This function fetches the number of new members joined today and overall.
        """
        with self.Session() as session:
            overall = session.query(func.count(User.userid))
            if only_today:
                return overall.filter(today.date() == User.datejoined).scalar()
            else:
                return overall.scalar()

    def get_sales_done(self, only_today=False):
        """
        This function retrieves the total sales (amount credited) done today and overall.
        """

        with (self.Session() as session):
            overall = session.query(func.sum(Transaction.amount_credited)
                                    ).filter("Recharge" != Transaction.transaction_detail)
            if only_today:
                overall = overall.filter(Transaction.transaction_date >= today.date())
            val = overall.scalar() or 0.0

            return -1 * val

    def get_total_recharge(self, only_today=False):
        """
        This function retrieves the total recharge amount for all time and today.
        """
        with self.Session() as session:
            overall = session.query(func.sum(Transaction.amount_credited)
                                    ).filter("Recharge" == Transaction.transaction_detail)
            if only_today:
                overall = overall.filter(Transaction.transaction_date >= today.date())
            return overall.scalar() or 0.0

    def get_all_data_today_and_overall(self):
        """
        This function combines all data retrieval into a single dictionary.
        """
        data = {
            'Joined': {'Today': self.get_new_members_joined(only_today=True),
                       'Overall': self.get_new_members_joined(only_today=False)},
            'Recharge': {'Today': self.get_total_recharge(only_today=True),
                         'Overall': self.get_total_recharge(only_today=False)},
            'Sales': {'Today': self.get_sales_done(only_today=True),
                      'Overall': self.get_sales_done(only_today=False)}
        }

        return data


class api_point:
    def __init__(self) -> None:
        try:
            try:
                from secrets_handler import VARIABLES
                postgreurl = VARIABLES["POSTGRESQL_DB"]
            except :
                from dotenv import load_dotenv
                load_dotenv()
                postgreurl:str|None = os.environ.get('POSTGRESQL_DB')
            
            self.user_db = UserDatabase(postgreurl)
        except BaseException as e:
            log(1, "Error Connecting with database")
            raise e

    def get_report(self):
        return self.user_db.get_all_data_today_and_overall()

    def see_balance(self, user_id) -> float:
        return float(self.user_db.get_user_balance(user_id)) # type: ignore

    def add_balance(self, user_id, amount) -> bool|None:
        try:
            self.user_db.record_transaction(user_id, 'Recharge', amount)
        except Exception:
            log(2, f"Unable to recharge {user_id} in the Database")
            return False

    def add_orders(self, user_id, transaction_detail, credit_to_user):
        try:
            self.user_db.record_transaction(
                user_id, transaction_detail, credit_to_user
            )
            return True
        except Exception as e:
            log(
                2, f"Unable to record txns {user_id, transaction_detail, credit_to_user}"
            )
            if 'Low balance' in str(e):
                return "You are running with low balance"
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
            return "Error Fetching Data"

    def get_favourite_services(self, user_id):
        most_bought = self.user_db.get_most_buyed(user_id)
        return most_bought

    def record_recharge(self, user_id, utr, amount: float):
        return self.user_db.add_recharge(user_id, amount, utr)


reception_api = api_point()


# Test Case
def test_debasish():
    myid = 8906421312
    reception_1 = reception_api

    # Check Recharge
    old_bal = reception_1.see_balance(myid)
    reception_1.record_recharge(user_id=myid, amount=10,utr=9876543216)
    new_bal = reception_1.see_balance(myid)
    assert old_bal + 10 == new_bal

    # Check Transactions
    reception_1.add_orders(myid, "A Test Transaction", 12)
    new_bal = reception_1.see_balance(myid)
    assert new_bal == old_bal - 12
    print(reception_1.see_transactions(myid))


def test_report():
    resp = reception_api.get_report()
    print(resp)
    assert isinstance(resp, dict)


if __name__ == '__main__':
    test_debasish()
