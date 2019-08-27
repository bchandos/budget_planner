import csv
import codecs

from bottle import Bottle, run, request

from import_transactions import parse_upload, import_all_transactions

app = Bottle()

@app.route('/', method='GET')
def upload_form():
    with open('upload_form.html') as f:
        x = f.readlines()
    return x

@app.route('/import_transactions', method='POST')
def importer():
    upload = codecs.iterdecode(request.files.get('file_upload').file, 'utf-8') #pylint: disable=no-member
    bank = request.forms.get('bank') #pylint: disable=no-member
    parsed = parse_upload(upload)
    import_all_transactions(parsed, bank)

    


run(app)