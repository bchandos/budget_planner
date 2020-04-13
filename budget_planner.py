import codecs
import csv
import json
from datetime import date

import dateparser
from bottle import Bottle, redirect, request, run, response
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.inspection import inspect

from db import session_scope
from import_transactions import import_all_transactions, parse_upload
from models import Account, Transaction, User, Category, AccountCategory

### temp code to load my account settings when I nuke the DB which I do frequently on account of being a dumbass
with session_scope() as session:
    if not session.query(Account).all():
        a = Account(name='Citi Costco',
                    debit_positive = True,
                    date_format = "%m/%d/%Y",
                    credit_map = "Credit",
                    debit_map = "Debit",
                    description_map = "Description",
                    date_map = "Date")
        
        b = Account(name='Capital One Checking',
                    debit_positive = False,
                    date_format = "%m/%d/%y",
                    credit_map = "Credit",
                    debit_map = "Debit",
                    description_map = "Description",
                    date_map = "Posted Date")
        c = Account(name='Capital One Quicksilver',
                    debit_positive = True,
                    date_format = "%m/%d/%Y",
                    credit_map = " Credit",
                    debit_map = " Debit",
                    description_map = " Description",
                    date_map = " Transaction Date",
                    category_map = " Category")
        session.add(a)
        session.add(b)
        session.add(c)
        session.commit()
#### end temp code

app = Bottle()

API_V = '/api/v0.1'

@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'PUT, GET, POST, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

@app.route('/', method = 'OPTIONS')
@app.route('/<path:path>', method = 'OPTIONS')
def options_handler(path = None):
    return

@app.route(f'/{API_V}', method='GET')
@app.route('/', method='GET')
def upload_form():
    with open('upload_form.html') as f:
        x = f.readlines()
    return x

@app.route(f'{API_V}/import_transactions', method='POST')
def importer():
    upload = codecs.iterdecode(request.files.get('file_upload').file, 'utf-8') #pylint: disable=no-member
    bank_id = request.forms.get('bank_id') #pylint: disable=no-member
    parsed = parse_upload(upload)
    with session_scope() as session:
        try:
            account = session.query(Account).get(int(bank_id))
        except Exception:
            response.status = 404
            return {'status': 'failed', 'payload': {'error_message': f'no account id {bank_id}'}}
        else:
            import_response = import_all_transactions(parsed, account.id)
            response.status = 201 if import_response.get('status') == 'success' else 404
            return import_response
        
@app.route(f'{API_V}/transactions', method='GET')
@app.route(f'{API_V}/transactions/account/<account_id:int>', method='GET')
@app.route(f'{API_V}/transactions/category/<category_id:int>', method='GET')
def transactions(account_id=None, category_id=None):
    with session_scope() as session:
        if account_id:
            trans = session.query(Account).get(account_id).transactions
        elif category_id:
            trans = session.query(Category).get(category_id).transactions
        else:
            trans = session.query(Transaction).all()
        
        if trans:
            status = 'success'
            payload = [row.asdict('account', 'category') for row in trans]
        else:
            status = 'failed'
            payload = {'error_message': f'no account id {account_id}'}
            response.status = 404
            
    return {'status': status, 'payload': payload}

@app.route(f'{API_V}/transaction', method='POST')
@app.route(f'{API_V}/transaction/<trans_id:int>', method=('GET', 'PUT', 'DELETE'))
def transaction(trans_id=None):
    if request.method == 'GET' and trans_id:
        with session_scope() as session:
            if trans_id:
                trans = session.query(Transaction).get(trans_id)
                if trans:
                    status = 'success'
                    payload = trans.asdict('account', 'category')
                else:
                    status = 'failed'
                    payload = {'error_message': f'no transaction id {trans_id}'}
                    response.status = 404
    
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
            response.status = 400
            return {'status': status, 'payload': payload}
        else:
            json_request['date'] = parsed_date                              #pylint: disable=unsupported-assignment-operation
        # make sure we supply a credit value, if not passed, to enforce UNIQUE constraint
        if not json_request.get('credit'):                                  #pylint: disable=no-member
            json_request['credit'] = 0                                      #pylint: disable=unsupported-assignment-operation
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
                response.status = 400
            else:
                status = 'success'
                payload = new_transaction.asdict('account', 'category')
                response.status = 201

    elif request.method == 'PUT' and trans_id and request.json:
        # update existing transaction id = trans_id
        json_request = request.json
        # format the date
        if json_request.get('date'): #pylint: disable=no-member
            json_request['date'] = dateparser.parse(json_request.get('date'))  #pylint: disable=unsupported-assignment-operation,no-member
        # should not be able to update an id
        if json_request.get('id'):  #pylint: disable=no-member
            json_request.pop('id') #pylint: disable=no-member
        for k, v in json_request.items():
            # serialized related objects need to be deserialized
            if k.endswith('_id') and type(v) == dict:
                json_request[k] = v.get('id')               
        with session_scope() as session:
            try:
                update = session.query(Transaction).filter(Transaction.id==trans_id).update(values=json_request) #pylint: disable=not-a-mapping
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
                    payload = transaction.asdict('account', 'category')
                    response.status = 201
                else:
                    status = 'failed'
                    payload = {'error_message': f'no transaction id {trans_id}'}
                    response.status = 404
    elif request.method == 'DELETE' and trans_id:
        with session_scope() as session:
            del_item = session.query(Transaction).get(trans_id)
            del_rows = session.query(Transaction).filter(Transaction.id==trans_id).delete()
            if del_rows > 1:
                session.rollback()
        if del_rows == 1:
            status = 'success'
            payload = del_item.asdict()
            # payload = {'message': f'successfully deleted transaction id {trans_id}'}
            response.status = 200
        else:
            status = 'failed'
            payload = {'error_message': f'could not delete or does not exist id {trans_id}'}
            response.status = 404

    else:
        status = 'failed'
        payload = {'error_message': 'not a valid request'}
        response.status = 400
    return {'status': status, 'payload': payload}

@app.route(f'{API_V}/transaction/<trans_id:int>/reconciliations', method=('GET',))
def reconciliations(trans_id):
    with session_scope() as session:
        transaction = session.query(Transaction).get(trans_id)
        if transaction:
            reconciliations = transaction.reconciliations
            payload = [r.asdict() for r in reconciliations]
            status = 'success'
            response.status = 200
        else:
            status = 'failed'
            payload = {'error_message': f'no transaction id {trans_id}'}
            response.status = 404

    return {'status': status, 'payload': payload}

@app.route(f'{API_V}/accounts', method=('GET', 'POST'))
@app.route(f'{API_V}/accounts/<account_id:int>', method=('GET', 'PUT', 'DELETE'))
def accounts(account_id=None):
    with session_scope() as session:
        if account_id: 
            if request.method == 'GET':
                # retrieve account by id
                account = session.query(Account).get(account_id)
                if account:
                    status = 'success'
                    payload = account.asdict()
                    response.status = 200
                else:
                    status = 'failed'
                    payload = {'error_message': f'no account id {account_id}'}
                    response.status = 404
            
            elif request.method == 'PUT':
                # update existing account and its settings
                json_request = request.json
                # updates shouldn't modify id
                if json_request.get('id'): #pylint: disable=no-member
                    json_request.pop('id') #pylint: disable=no-member
                for k, v in json_request.items():
                    # serialized related objects need to be deserialized
                    if k.endswith('_id') and type(v) == dict:
                        json_request[k] = v.get('id')
                account = session.query(Account).get(account_id)
                if not account:
                    status = 'failed'
                    payload = {'error_message': f'account id {account_id} does not exist'}
                    response.status = 404
                else:
                    for k in json_request: #pylint: disable=not-an-iterable
                        setattr(account, k, json_request[k]) #pylint: disable=unsubscriptable-object
                    status = 'success'
                    payload = account.asdict()
                    response.status = 201

            elif request.method == 'DELETE':
                # delete existing account
                del_item = session.query(Account).get(account_id)
                del_rows = session.query(Account).filter(Account.id==account_id).first()
                try:
                    session.delete(del_rows)
                    session.commit()
                except Exception as err:
                    session.rollback()
                    print(err)
                    status = 'failed'
                    payload = {'error_message': f'could not delete or does not exist id {account_id}'}
                    response.status = 404
                else:
                    status = 'success'
                    payload = del_item.asdict()
                    # payload = {'message': f'successfully deleted transaction id {account_id}'}
                    response.status = 200

        elif request.method == 'GET':
            # get all accounts
            accounts = session.query(Account).all()
            if accounts:
                status = 'success'
                payload = [account.asdict() for account in accounts]
                response.status = 200
            else:
                status = 'success'
                payload = []
                response.status = 200
        elif request.method == 'POST':
            # create new account
            json_request = request.json
            # remove any invalid column values
            for k in list(json_request):
                if k not in Account.__table__.columns.keys(): #pylint: disable=no-member
                    json_request.pop(k) #pylint: disable=no-member
            # new accounts should not receive an id
            if json_request.get('id'): #pylint: disable=no-member
                json_request.pop('id') #pylint: disable=no-member
            new_account = Account(**json_request) #pylint: disable=not-a-mapping
            try:
                session.add(new_account)
                session.commit()
            except IntegrityError as err:
                session.rollback()
                status = 'failed'
                error_message = str(err).split(':')[0]
                payload = {'error_message': error_message}
                response.status = 400
            else:
                status = 'success'
                payload = new_account.asdict()
                response.status = 201
        
    return {'status': status, 'payload': payload}

@app.route(f'{API_V}/transaction/<transaction_id:int>/related', method='GET')
def related_transactions(transaction_id):
    # Find transactions that may be related to another transaction
    with session_scope() as session:
        transaction = session.query(Transaction).get(transaction_id)
        related_transactions = session.query(Transaction).filter(Transaction.amount==-transaction.amount, Transaction.account!=transaction.account).all()
        if transaction:
            status = 'success'
            payload = [row.asdict() for row in related_transactions if row.id != transaction_id]
            response.status = 200
        else:
            status = 'failed'
            payload = f'no transaction or related transactions id {transaction_id}'
            response.status = 404

        return {'status': status, 'payload': payload}

@app.route(f'{API_V}/categories', method=('GET', 'POST'))
def categories():
    with session_scope() as session:
        if request.method == 'GET':
            categories = session.query(Category).order_by(Category.name).all()
            if categories:
                status = 'success'
                payload = [category.asdict() for category in categories]
                response.status = 200
            else:
                status = 'success'
                payload = []
                response.status = 200
        elif request.method == 'POST':
            # create new category
            json_request = request.json
            # remove any invalid column values
            for k in list(json_request):
                if k not in Category.__table__.columns.keys(): #pylint: disable=no-member
                    json_request.pop(k) #pylint: disable=no-member
            # new categories should not receive an id
            if json_request.get('id'): #pylint: disable=no-member
                json_request.pop('id') #pylint: disable=no-member
            new_category = Category(**json_request) #pylint: disable=not-a-mapping
            try:
                session.add(new_category)
                session.commit()
            except IntegrityError as err:
                session.rollback()
                status = 'failed'
                error_message = str(err).split(':')[0]
                payload = {'error_message': error_message}
                response.status = 400
            else:
                status = 'success'
                payload = new_category.asdict()
                response.status = 201
    
    return {'status': status, 'payload': payload}

run(app)
