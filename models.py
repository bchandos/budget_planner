from decimal import Decimal
from datetime import datetime, date

import sqlalchemy.types as types
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint, DateTime
from sqlalchemy.ext.declarative import as_declarative, declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect


class B:
    def _asdict(self, *args):
        """Returns database objects as a dictionary. Optionally accepts
        column names as args to convert to type_, which by default is string.
        This is because bottle's built-in JSON serializer can't handle 
        Date or Decimal objects."""
        dict_ = {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}
        for arg in args:
            if isinstance(dict_[arg], Decimal):
                dict_[arg] = float(dict_[arg])
            elif isinstance(dict_[arg], datetime):
                dict_[arg] = str(dict_[arg].isoformat())
            elif isinstance(dict_[arg], date):
                dict_[arg] = str(dict_[arg].isoformat())
        return dict_


Base = declarative_base(cls=B)

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
    # Settings
    filename_re = Column(String)
    debit_positive = Column(Boolean)
    date_format = Column(String)
    field_mappings = Column(String)
    # Relationship
    transactions = relationship('Transaction', cascade='all,delete')

class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(Integer, primary_key=True)
    account = Column(ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime)
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
