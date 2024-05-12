from flask import Flask, render_template, redirect, request
import requests
import os
from datetime import date
from dotenv import load_dotenv
load_dotenv()  # This reads the .env file
API_KEY = os.environ.get('API_KEY')

app = Flask(__name__)

url = "https://endgrate.com/api/pull/initiate"

payload = { "provider": "asana", "schema": [{ "endgrate_type": "workspace-task" }] }
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {API_KEY}"
}
response = requests.post(url, json=payload, headers=headers)
print(response.text)
id_asana = response.json()["session_id"]

url = "https://endgrate.com/api/session/initiate"

payload = { "provider": "todoist", "schema": [{ "endgrate_type": "workspace-task" }] }
headers = {
    "accept": "application/json",
    "content-type": "application/json",
    "authorization": f"Bearer {API_KEY}"
}
response = requests.post(url, json=payload, headers=headers)
id_todoist = response.json()["session_id"]


AUTHENTICATEDASANA = False
AUTHENTICATEDTODOIST = False

def get_asana_data():
    payload = { 
        "session_id": id_asana,
        "endgrate_type": "workspace-task",
        "synchronous": True,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}"
    }

    response = requests.post("https://endgrate.com/api/pull/transfer", json=payload, headers=headers)
    transfer_id = response.json()["transfer_id"]

    url = f"https://endgrate.com/api/pull/data?endgrate_type=workspace-task&transfer_id={transfer_id}"
    response = requests.get(url, headers={"accept": "application/json", "authorization": f"Bearer {API_KEY}"})
    data = response.json()
    mdata = {task["id"]:task["data"] for task in data["transfer_data"]}
    return mdata

def push_to_todoist(task):
    payload = {
        "session_id": id_todoist,
        "endgrate_type": "workspace-task",
        "transfer_data": [{ "data": task }]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}"
    }
    print(payload)

    response = requests.post("https://endgrate.com/api/push/transfer", json=payload, headers=headers)
    print(response)

@app.route('/')
def index():
    return render_template('index.html', id=id_asana)

@app.route('/auth-asana')
def auth_asana():
    global AUTHENTICATEDASANA
    AUTHENTICATEDASANA = True
    return redirect("https://endgrate.com/session?session_id=" + id_asana)

@app.route('/auth-todoist')
def auth_todoist():
    global AUTHENTICATEDTODOIST
    AUTHENTICATEDTODOIST = True
    return redirect("https://endgrate.com/session?session_id=" + id_todoist)

@app.route('/tasks')
def tasks():
    if AUTHENTICATEDASANA:
        data = get_asana_data()
        return render_template('tasks.html', tasks=data)
    
@app.route('/push')
def push():
    if AUTHENTICATEDTODOIST:
        subject = request.args.get("subject")
        date = request.args.get("date", "")
        task = {
            'completed_date': '',
            'content': subject,
            'due_date': date,
            'status': '',
            'subject': '',
        }
        push_to_todoist(task)
    return redirect('/tasks')
    
@app.route('/pushall')
def pushall():
    data = get_asana_data()
    today = date.today()
    if AUTHENTICATEDTODOIST:
        for d in list(data.values()):
            task = {
                'completed_date': '',
                'content': d['subject'],
                'due_date': f'{today}',
                'status': '',
                'subject': '',
            }
            push_to_todoist(task)
    return redirect('/tasks')

app.run(host='localhost', port=5100)