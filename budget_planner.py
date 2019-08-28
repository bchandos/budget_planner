import csv
import codecs

from bottle import Bottle, run, request, redirect
from sqlalchemy.inspection import inspect

from import_transactions import parse_upload, import_all_transactions
from models import Transaction, User, Account
from db import session_scope

app = Bottle()

API_V = '/api/v0.1'

@app.route('/', method='GET')
def upload_form():
    with open('upload_form.html') as f:
        x = f.readlines()
    return x

@app.route(f'{API_V}/import_transactions', method='POST')
def importer():
    upload = codecs.iterdecode(request.files.get('file_upload').file, 'utf-8') #pylint: disable=no-member
    bank = request.forms.get('bank') #pylint: disable=no-member
    parsed = parse_upload(upload)
    import_stats = import_all_transactions(parsed, bank)
    status = 'success'
    response_dict = {'status': status, 'payload': import_stats}

    return response_dict

@app.route(f'{API_V}/transactions/<account_id:int>')
def transactions(account_id=None):
    with session_scope() as session:
        if account_id:
            trans = session.query(Transaction).filter(Transaction.account==account_id).all()
            trans_array = [row._asdict() for row in trans]
        status = 'success'
        response_dict = {'status': status, 'payload': trans_array}

    return response_dict

run(app)