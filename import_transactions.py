import csv
import os
import re
from itertools import chain

from json_settings import JSONSettings
from models import Transaction

settings = JSONSettings(
    'settings.json', settings_template='settings-example.json')


def import_all_transactions(filename, bank):
    # import all transactions from csv file
    # filename is provided from upload and storage routines
    # bank indicates which header matching to use
    field_matchings = settings.get_setting('file_formats', 'bank')['field_matchings']
    with open(filename, newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            transaction = Transaction(account=row.get(field_matchings.get('account')),
                                      date=row.get(field_matchings.get('date')),
                                      description=row.get(field_matchings.get('description')),
                                      category=row.get(field_matchings.get('category')),
                                      credit=row.get(field_matchings('credit')),
                                      debit=row.get(field_matchings('debit')),
                                      amount=None)
            transaction.save()