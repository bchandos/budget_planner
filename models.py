from decimal import Decimal
from datetime import datetime, date

import sqlalchemy.types as types
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint, DateTime
from sqlalchemy.ext.declarative import as_declarative, declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect


class B:
    def asdict(self):
        """Returns database objects as a dictionary. Checks each value
        to see if is an instance of either Decimale or Datetime, and converts.
        This is because bottle's built-in JSON serializer can't handle 
        Date or Decimal objects."""
        dict_ = {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}
        for arg in dict_:
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
    # Field Mappings
    credit_map = Column(String)
    debit_map = Column(String)
    description_map = Column(String)
    date_map = Column(String)
    category_map = Column(String)
    # Relationship
    transactions = relationship('Transaction', cascade='all,delete')

class Transaction(Base):
    __tablename__ = 'transaction'

    id = Column(Integer, primary_key=True)
    account = Column(ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime)
    description = Column(String)
    category = Column(ForeignKey('category.id', ondelete='CASCADE'), nullable=True)
    credit = Column(Numeric)
    debit = Column(Numeric)
    # perhaps the above should just be....
    amount = Column(Numeric)
    # with positive or negative values
    reconciled = Column(Boolean)
    reconcile_to = Column(ForeignKey('transaction.id'))  # does this work?
    UniqueConstraint(account, date, description, credit, debit, name='uix_1')


class Category(Base):
    __tablename__ = 'category'
    # Describes a system level transaction category
    id = Column(Integer, primary_key=True)
    name = Column(String)
    # Relationship
    transactions = relationship('Transaction')
    account_categories = relationship('AccountCategory')


class AccountCategory(Base):
    __tablename__ = 'account_category'
    # Describes a account defined category, to be matched with an internal category
    id = Column(Integer, primary_key=True)
    name = Column(String)
    account = Column(ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    category = Column(ForeignKey('category.id', ondelete='CASCADE'), nullable=True)