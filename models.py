from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.inspection import inspect

@as_declarative()
class Base:
    def _asdict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}


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
    UniqueConstraint(account, date, description, credit, debit, name='uix_1')
