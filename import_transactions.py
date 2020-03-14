import csv
import json
import os
import re
from datetime import date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from db import session_scope
from models import Account, Transaction, AccountCategory, Category

def parse_upload(file_object):
    """
    Parse the POST request containing the csv file, extract. Using
    csv.DictReader, generated list of OrderedDicts
    
    :param file_object: file-like object representing the CSV upload
    :type file_object: object
    :returns: a list of OrderedDicts containing all rows of the CSV file
    :rtype: list
    :raise KeyError: raises an exception
    """

    # check integrity of data somehow
    reader = csv.DictReader(file_object)
    return [row for row in reader]
    

def import_all_transactions(csv_dict, account_id):
    """
    Given the DictReader results from the csv file import, as well as 
    the bank name, imports transactions to database. Uses bank's field
    matching attributes.
    
    :param csv_dict: DictReader results from parse_upload
    :type csv_dict: list
    :param account_id: account id
    :type account_id: int
    :returns: added and skipped record counts
    :rtype: dict
    :raise Exception: raises an exception
    """

    with session_scope() as session:
        account = session.query(Account).get(account_id)
        # Sanity check to confirm the account we've provided matches
        # the CSV data provided
        field_maps = [account.credit_map,
                      account.debit_map,
                      account.description_map,
                      account.date_map,
                      account.category_map]
        errors = 0
        for field_map in field_maps:
            if field_map not in csv_dict[0].keys():
                errors += 1
        if errors > 1: # we'll allow one field to be off?
            return {'status': 'failed', 'payload': {'error_message': 'field mapping does not align with uploaded file'}}

        added = 0
        skipped = 0
        new_transactions = list()
        for row in csv_dict:
            amount = 0
            trans_date = datetime.strptime(row.get(account.date_map), account.date_format)
            if row.get(account.credit_map):
                credit = float(row.get(account.credit_map))
                amount = credit
            else:
                credit = 0
            if row.get(account.debit_map):
                debit = float(row.get(account.debit_map))
                amount = debit * -1 if account.debit_positive else debit
            else:
                debit = 0
            # Handle categories...
            if row.get(account.category_map):
                account_category = session.query(AccountCategory).filter(AccountCategory.name==row.get(account.category_map)).one_or_none()
                if not account_category:
                    account_category = AccountCategory(name=row.get(account.category_map), account=account.id)
                    session.add(account_category)
                    session.commit()
                
                if account_category.category:
                    category_id = account_category.category
                else:
                    category = session.query(Category).filter(Category.name==account_category.name).one_or_none()
                    if not category:
                        category = Category(name=account_category.name)
                        session.add(category)
                        session.commit()
                    account_category.category = category.id
                    category_id = category.id
            else:
                category_id = None
            
            transaction = Transaction(account=account.id,
                                    date=trans_date,
                                    description=row.get(account.description_map),
                                    category=category_id,
                                    credit=credit,
                                    debit=debit,
                                    amount=amount)
            try:
                session.add(transaction)
                session.commit()
            except IntegrityError:
                session.rollback()
                skipped += 1
            else:
                added += 1
                new_transactions.append(transaction.asdict())

        return {'status': 'success', 
                'payload': 
                    {'total': added + skipped, 
                    'added': added, 
                    'skipped': skipped, 
                    'new_transactions': new_transactions}
                }
