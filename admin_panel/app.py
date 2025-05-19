from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(name)

@app.route('/')
def index():
    return render_template('index.html')

if name == 'main':
    app.run(debug=True, host='0.0.0.0', port=5000)



# Настройки
SPREADSHEET_NAME = 'Экскурсии'
CREDENTIALS_FILE = 'credentials.json'

# Flask-приложение
app = Flask(__name__)


# Получение таблицы
def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).sheet1
    return sheet


@app.route('/')
def index():
    sheet = get_sheet()
    records = sheet.get_all_records()

    # Фильтры
    route = request.args.get('route')
    date = request.args.get('date')
    filtered = [r for r in records if
                (not route or route.lower() in r['Маршрут'].lower()) and
                (not date or date in r['Дата'])]

    return render_template('index.html', records=filtered, route=route or '', date=date or '')


if __name__ == '__main__':
    app.run(debug=True)
