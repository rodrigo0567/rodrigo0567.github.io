from flask import Flask, render_template, request, redirect, url_for,session
import random
import gspread
from google.oauth2.service_account import Credentials
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from werkzeug.utils import secure_filename
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv
import json
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_PY')

app.config['ALLOWED_EXTENSIONS'] = set(os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif').split(','))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
creds = Credentials.from_service_account_info(creds_json, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])


client = gspread.authorize(creds)
spreadsheet = client.open('CONVIDADOS CONFIRMADOS')  
worksheet = spreadsheet.get_worksheet(0) 

creds1_json = json.loads(os.getenv("GOOGLE_MUSIC_CREDENTIALS_JSON"))
creds1 = Credentials.from_service_account_info(creds1_json, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])


client1 = gspread.authorize(creds1)
spreadsheet1 = client1.open('MÚSICA')  
worksheet1 = spreadsheet1.get_worksheet(0) 


questions = [
    {
        "question": "Quantos anos eu faço esse ano?",
        "options": ["20", "19", "21"],
        "correct": "20"
    },
    {
        "question": "Qual curso faço?",
        "options": ["Ciência de Dados", "Ciência da Computação", "Ciência para Negócios"],
        "correct": "Ciência da Computação"
    },
    {
        "question": "Qual minha cor favorita?",
        "options": ["Preto", "Branco", "Roxo"],
        "correct": "Preto"
    },
    {
        "question": "Num ninho de mafagafos há 7 mafagafinhos, quando a mafagafa gafa, gafam...",
        "options": ["Todos os mafagafinhos", "Os 7 mafagafinhos", "Nenhum mafagafinho"],
        "correct": "Os 7 mafagafinhos"
    }
]

confirmed_guests = []

@app.route('/')
def home():
    # Seleciona uma pergunta aleatória
    selected_question = random.choice(questions)
    return render_template('home.html', question=selected_question)

@app.route('/validate_answer', methods=['POST'])
def validate_answer():
    question = request.form.get('question')
    selected_answer = request.form.get('answer')

    # Busca a pergunta correspondente e valida
    for q in questions:
        if q["question"] == question:
            if selected_answer == q["correct"]:
                return redirect(url_for('main'))
            break

    # Resposta incorreta, redireciona com erro
    return redirect(url_for('home') + '?error=true')

@app.route('/main')
def main():
    return render_template('main.html')

@app.route('/confirm')
def confirm():
    return render_template('confirm.html')

@app.route('/save_confirmation', methods=['POST'])
def save_confirmation():
    name = request.form.get('name')
    if name:
        # Enviar o nome para a planilha
        worksheet.append_row([name])  # Adiciona o nome na próxima linha da planilha
    return redirect(url_for('main'))



@app.route('/add_music', methods=['GET', 'POST'])
def add_music():
    status = request.args.get('status')  # Captura o status da URL

    if request.method == 'POST':
        music_name = request.form.get('music')
        artist_name = request.form.get('artist')  # Adiciona o campo do artista

        if music_name and artist_name:
            try:
                worksheet1.append_row([music_name, artist_name])
                return redirect(url_for('add_music', status='success'))  # Redireciona com status de sucesso
            except Exception as e:
                print(f"Erro ao salvar na planilha: {e}")
                return redirect(url_for('add_music', status='error'))  # Redireciona com status de erro
    
    return render_template('add_music.html', status=status)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
