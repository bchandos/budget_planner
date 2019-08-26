import csv
import os
import re

from json_settings import JSONSettings
from models import Transaction, Account
from db import session_scope

settings = JSONSettings(
    'settings.json', settings_template='settings-example.json')

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
    with open(file_object, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        return [row for row in reader]
    

def import_all_transactions(csv_dict, bank):
    """
    Given the DictReader results from the csv file import, as well as 
    the bank id, imports transactions to database. Uses bank's field
    matching attributes.
    
    :param csv_dict: DictReader results from parse_upload
    :type csv_dict: list
    :param bank: bank identifier
    :type bank: str
    :returns: None
    :rtype: None
    :raise Exception: raises an exception
    """

    field_matchings = settings.get_setting('file_formats', 'bank')['field_matchings']
    with session_scope() as session:    
        for row in csv_dict:
            account = session.query(Account, name=field_matchings.get('account'))
            transaction = Transaction(account=account,
                                    date=row.get(field_matchings.get('date')),
                                    description=row.get(field_matchings.get('description')),
                                    category=row.get(field_matchings.get('category')),
                                    credit=row.get(field_matchings('credit')),
                                    debit=row.get(field_matchings('debit')),
                                    amount=None)
            session.add(transaction)