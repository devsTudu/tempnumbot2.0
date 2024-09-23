from logging import log
from os import getenv
from dotenv import load_dotenv
import datetime

load_dotenv()

from sqlalchemy import (
    create_engine,
    Column,
    Integer,BigInteger,
    Float,
    Date,
    Text,
    TIMESTAMP,
    UniqueConstraint,
    ForeignKey,
    func
)

from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError


Base = declarative_base()


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


class Service(Base):
    __tablename__ = "services"

    service_id = Column(Integer, primary_key=True)
    service_name = Column(Text, unique=True)
    price = Column(Float)
    service_code = Column(Text, unique=True)

class Recharges(Base):
    __tablename__ = "recharge_list"
    utr_no = Column(Text,primary_key=True)
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

    def get_most_buyed(self,user_id):
        with self.Session() as session:
            lis = session.query(Transaction.transaction_detail,
                          func.count(Transaction.transaction_detail
                                     ).label('count')
                          ).filter(Transaction.userid == user_id
                                   ).filter(Transaction.amount_credited < 0).group_by(Transaction.transaction_detail
                                   ).order_by(func.count(Transaction.transaction_detail).desc()
                                              ).all()
            
            return [item.transaction_detail for item in lis]
    def add_recharge(self,user_id,amount,utr):
        with self.Session() as session:
            new_recharge = Recharges(userid=user_id, amount=abs(amount), utr_no=str(utr))
            log(1,f'Checking recharge at {utr}')
            try:
                session.add(new_recharge)
                session.commit()
                self.record_transaction(user_id,'Recharge',abs(amount))
                return True
            except IntegrityError as i:
                return False
            except Exception as e:
                log(2,"Recharge Recording Issue")
                raise e

class api_point:
    def __init__(self) -> None:
        try:    
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
            self.user_db.record_transaction(user_id,'Recharge',amount)
        except Exception:
            log(2, f"Unable to recharge {user_id} in the Database")
            return False

    def add_orders(self, user_id, transaction_detail, cost):
        try:
            self.user_db.record_transaction(
                user_id, transaction_detail, cost
            )
            return True
        except Exception as e:
            log(
                2, f"Unable to record txns {user_id,transaction_detail,cost}"
            )
            print(e)
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

    def record_recharge(self,user_id,utr,amount:float):
        return self.user_db.add_recharge(user_id,amount,utr)
        


reception_api = api_point()


# Test Case
def test_debasish():
    myid = 8906421312
    reception_1 = reception_api

    # Check Recharge
    old_bal = reception_1.see_balance(myid)
    reception_1.record_recharge(user_id=myid, amount=10)
    new_bal = reception_1.see_balance(myid)
    assert old_bal + 10 == new_bal

    # Check Transactions
    reception_1.add_orders(myid, "A Test Transaction", 12)
    new_bal = reception_1.see_balance(myid)
    assert new_bal == old_bal - 2
    print(reception_1.see_transactions(myid))



if __name__=='__main__':
    test_debasish()


