from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    nickname = Column(String)


class Account(Base):
    __tablename__ = 'account'

    id = Column(Integer, primary_key=True)
    name = Column(String)


class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(Integer, primary_key=True)
    account = Column(ForeignKey('account.id'))
    date = Column(Date)
    description = Column(String)
    category = Column(String)
    credit = Column(Numeric)
    debit = Column(Numeric)
    # perhaps the above should just be....
    amount = Column(Numeric)
    # with positive or negative values
    reconciled = Column(Boolean)
    reconcile_to = Column(ForeignKey('transaction.id'))  # does this work?
