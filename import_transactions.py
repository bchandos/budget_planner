import csv
import json
import os
import re
from datetime import date, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from db import session_scope
from json_settings import JSONSettings
from models import Account, Transaction, AccountSettings

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
        settings = session.query(AccountSettings).filter(AccountSettings.account==account_id).one()
        account = session.query(Account).get(account_id)
        field_matchings = json.loads(settings.field_mappings)

        added = 0
        skipped = 0    
        for row in csv_dict:
            trans_date = datetime.strptime(row.get(field_matchings.get('date')), settings.date_format)
            if row.get(field_matchings.get('credit')):
                credit = float(row.get(field_matchings.get('credit')))
            else:
                credit = 0
            if row.get(field_matchings.get('debit')):
                debit = float(row.get(field_matchings.get('debit')))
            else:
                debit = 0
            transaction = Transaction(account=account.id,
                                    date=trans_date,
                                    description=row.get(field_matchings.get('description')),
                                    category=row.get(field_matchings.get('category')),
                                    credit=credit,
                                    debit=debit,
                                    amount=None)
            try:
                session.add(transaction)
                session.commit()
            except IntegrityError:
                session.rollback()
                skipped += 1
            else:
                added += 1

        return {'total': added + skipped, 'added': added, 'skipped': skipped}
