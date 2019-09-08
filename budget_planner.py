import codecs
import csv
import json
from datetime import date

import dateparser
from bottle import Bottle, redirect, request, run
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.inspection import inspect

from db import session_scope
from import_transactions import import_all_transactions, parse_upload
from models import Account, Transaction, User, AccountSettings

### temp code to load my account settings when I nuke the DB which I do frequently on account of being a dumbass
with session_scope() as session:
    if not session.query(AccountSettings).filter(AccountSettings.account==1).one_or_none():
        ax = AccountSettings(account=1,
                            filename_re = r"Since (\D{3}) (\d+), (\d+).csv",
                            debit_positive = True,
                            date_format = "%m/%d/%Y",
                            field_mappings = json.dumps({"account": None, "credit": "Credit", "debit": "Debit", "description": "Description", "date": "Date"}))
        session.add(ax)
        session.commit()
#### end temp code

app = Bottle()

API_V = '/api/v0.1'

@app.route(f'/{API_V}', method='GET')
@app.route('/', method='GET')
def upload_form():
    with open('upload_form.html') as f:
        x = f.readlines()
    return x

@app.route(f'{API_V}/import_transactions', method='POST')
def importer():
    upload = codecs.iterdecode(request.files.get('file_upload').file, 'utf-8') #pylint: disable=no-member
    bank_name = request.forms.get('bank') #pylint: disable=no-member
    parsed = parse_upload(upload)
    with session_scope() as session:
        try:
            account = session.query(Account).filter(Account.name==bank_name).one()
        except MultipleResultsFound:
            raise
        except NoResultFound:
            account = Account(name=bank_name)
            session.add(account)
            session.commit()

        import_stats = import_all_transactions(parsed, account.id)
    
    status = 'success'
    return {'status': status, 'payload': import_stats}

@app.route(f'{API_V}/transactions', method='GET')
@app.route(f'{API_V}/transactions/<account_id:int>', method='GET')
def transactions(account_id=None):
    with session_scope() as session:
        if account_id:
            trans = session.query(Transaction).filter(Transaction.account==account_id).all()
        else:
            trans = session.query(Transaction).all()
        
        if trans:
            status = 'success'
            payload = [row._asdict('date', 'credit', 'debit', 'amount') for row in trans]
        else:
            status = 'failed'
            payload = {f'no account id {account_id}'}
            
    return {'status': status, 'payload': payload}

@app.route(f'{API_V}/transaction', method='POST')
@app.route(f'{API_V}/transaction/<trans_id:int>', method=('GET', 'PUT'))
def transaction(trans_id=None):
    if request.method == 'GET' and trans_id:
        with session_scope() as session:
            if trans_id:
                trans = session.query(Transaction).get(trans_id)
                if trans:
                    status = 'success'
                    payload = trans._asdict('date', 'credit', 'debit', 'amount')
                else:
                    status = 'failed'
                    payload = {'error_message': f'no transaction id {trans_id}'}
    
    elif request.method == 'POST' and request.json:
        # create a new transaction, ignores trans_id
        json_request = request.json
        # remove any invalid column values
        for k in list(json_request):
            if k not in Transaction.__table__.columns.keys():               #pylint: disable=no-member
                json_request.pop(k)                                         #pylint: disable=no-member
        # new transactions should not receive an id
        if json_request.get('id'):                                          #pylint: disable=no-member
            json_request.pop('id')                                          #pylint: disable=no-member
        # format the date
        parsed_date = dateparser.parse(json_request.get('date'))            #pylint: disable=no-member
        if not parsed_date:
            status = 'failed'
            payload = {'error_message': 'date missing or invalid format'}
            return {'status': status, 'payload': payload}
        else:
            json_request['date'] = parsed_date                              #pylint: disable=unsupported-assignment-operation
        # make sure we supply a credit value, if not passed, to enforce UNIQUE constraint
        if not json_request.get('credit'):
            json_request['credit'] = 0
        with session_scope() as session:
            new_transaction = Transaction(**json_request)                   #pylint: disable=not-a-mapping
            try:
                session.add(new_transaction)
                session.commit()
            except IntegrityError as err:
                session.rollback()
                status = 'failed'
                error_message = str(err).split(':')[0]
                payload = {'error_message': error_message}
            else:
                status = 'success'
                payload = new_transaction._asdict('date', 'credit', 'debit', 'amount')

    elif request.method == 'PUT' and trans_id and request.json:
        # update existing transaction id = trans_id
        json_request = request.json
        # format the date
        parsed_date = dateparser.parse(json_request.get('date'))            #pylint: disable=no-member
        if not parsed_date:
            status = 'failed'
            payload = {'error_message': 'date missing or invalid format'}
            return {'status': status, 'payload': payload}
        else:
            json_request['date'] = parsed_date                              #pylint: disable=unsupported-assignment-operation
        # should not be able to update an id
        if json_request.get('id'):                                          #pylint: disable=no-member
            json_request.pop('id')                                          #pylint: disable=no-member
        with session_scope() as session:
            try:
                update = session.query(Transaction).filter(Transaction.id==trans_id).update(values=json_request)     #pylint: disable=not-a-mapping
            except IntegrityError as err:
                session.rollback()
                status = 'failed'
                error_message = str(err).split(':')[0]
                payload = {'error_message': error_message}
            else:
                if update > 0:
                    session.commit()
                    status = 'success'
                    transaction = session.query(Transaction).get(trans_id)
                    payload = transaction._asdict('date', 'credit', 'debit', 'amount')
                else:
                    status = 'failed'
                    payload = {'error_message': f'no transaction id {trans_id}'}
    else:
        status = 'failed'
        payload = {'error_message': 'not a valid request'}
    return {'status': status, 'payload': payload}

@app.route(f'{API_V}/accounts')
@app.route(f'{API_V}/accounts/<account_id:int>')
def accounts(account_id=None):
    with session_scope() as session:
        if account_id:
            accounts = session.query(Account).get(account_id)
            status = 'success'
            payload = accounts._asdict()
        else:
            accounts = session.query(Account).all()
            status = 'success'
            payload = [row._asdict() for row in accounts]
        
        if not accounts:
            status = 'failed'
            payload = {f'no account id {account_id}'}
            
    return {'status': status, 'payload': payload}


run(app)
