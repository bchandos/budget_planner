from decimal import Decimal
from datetime import datetime, date

import sqlalchemy.types as types
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Numeric, String, UniqueConstraint, DateTime
from sqlalchemy.ext.declarative import as_declarative, declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect


class B:
    def asdict(self, *args):
        """Returns database objects as a dictionary. Checks each value
        to see if is an instance of either Decimale or Datetime, and converts.
        This is because bottle's built-in JSON serializer can't handle 
        Date or Decimal objects."""
        return_dict = {c.key: getattr(self, c.key)
                       for c in inspect(self).mapper.column_attrs}
        # fk_dict = {c.key: c.foreign_keys.pop()
        #            for c in inspect(self).mapper.columns if c.foreign_keys}
        for key, val in return_dict.items():
            if isinstance(val, Decimal):
                return_dict[key] = float(val)
            elif isinstance(val, datetime):
                return_dict[key] = val.isoformat()
            elif isinstance(val, date):
                return_dict[key] = str(val.isoformat())
            elif isinstance(val, bytes):
                return_dict[key] = None
            elif args:
                for arg in args:
                    if key == f'{arg}_id':
                        rel = getattr(self, arg)
                        return_dict[key] = rel.asdict() if rel else {}

        return return_dict


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
    account_id = Column(ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime)
    description = Column(String)
    category_id = Column(ForeignKey('category.id', ondelete='CASCADE'), nullable=True)
    credit = Column(Numeric)
    debit = Column(Numeric)
    # perhaps the above should just be....
    amount = Column(Numeric)
    # with positive or negative values
    reconciled = Column(Boolean)
    reconcile_to = Column(ForeignKey('transaction.id'))  # does this work?
    UniqueConstraint(account_id, date, description, credit, debit, name='uix_1')
    # Relationship
    reconciliations = relationship('Transaction')
    account = relationship('Account')
    category = relationship('Category')


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
    # Describes an account defined category, to be matched with an internal category
    id = Column(Integer, primary_key=True)
    name = Column(String)
    account = Column(ForeignKey('account.id', ondelete='CASCADE'), nullable=False)
    category = Column(ForeignKey('category.id', ondelete='CASCADE'), nullable=True)