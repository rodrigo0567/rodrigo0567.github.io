from flask import Flask, render_template, request, redirect, url_for,session
import random
import gspread
from google.oauth2.service_account import Credentials
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
import json
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_PY')

app.config['ALLOWED_EXTENSIONS'] = set(os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,gif').split(','))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

SCOPE = "playlist-modify-public playlist-modify-private"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                                client_secret=SPOTIPY_CLIENT_SECRET,
                                                redirect_uri=SPOTIPY_REDIRECT_URI,
                                                scope=SCOPE))


creds_json = json.loads(os.getenv("GOOGLE_CREDENTIALS_JSON"))
creds = Credentials.from_service_account_info(creds_json, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])


client = gspread.authorize(creds)
spreadsheet = client.open('CONVIDADOS CONFIRMADOS')  
worksheet = spreadsheet.get_worksheet(0) 
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

@app.route('/login')
def login():
    # Se o token já existe e não está expirado, redireciona para /add_music
    if 'token_info' in session:
        if not sp.auth_manager.is_token_expired(session['token_info']):
            return redirect(url_for('add_music'))

    # Gera a URL de autenticação do Spotify e redireciona
    auth_url = sp.auth_manager.get_authorize_url()
    return redirect(auth_url)


@app.route('/callback')
def callback():
    # Captura o código da URL após o usuário autenticar
    code = request.args.get('code')

    if not code:
        return "Erro: Código de autenticação não recebido.", 400

    # Troca o código pelo token de acesso
    token_info = sp.auth_manager.get_access_token(code)

    # Armazena o token na sessão
    session['token_info'] = token_info

    # Redireciona para a página de adicionar músicas
    return redirect(url_for('add_music'))


@app.route('/add_music', methods=['GET', 'POST'])
def add_music():
    if 'token_info' not in session:
        return redirect(url_for('login'))

    # Garante que o token esteja atualizado antes de fazer qualquer requisição
    token_info = session['token_info']
    if sp.auth_manager.is_token_expired(token_info):
        session['token_info'] = sp.auth_manager.refresh_access_token(token_info['refresh_token'])

    sp_client = spotipy.Spotify(auth=session['token_info']['access_token'])

    if request.method == 'POST':
        music_name = request.form['music']

        try:
            results = sp_client.search(q=music_name, type='track', limit=1)
            if results['tracks']['items']:
                track_uri = results['tracks']['items'][0]['uri']
                playlist_id = os.getenv('PLAYLIST_ID')
                sp_client.playlist_add_items(playlist_id, [track_uri])
                return redirect(url_for('add_music', status='success'))
            else:
                return redirect(url_for('add_music', status='error'))
        except Exception as e:
            print(f"Erro: {e}")
            return f"Ocorreu um erro: {e}"
    
    return render_template('add_music.html', status=request.args.get('status'))


@app.route('/add_photos', methods=['GET', 'POST'])
def add_photos():
    # Define a pasta de uploads dentro de static
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

    # Cria a pasta se não existir
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    if request.method == 'POST':
        if 'photo' not in request.files:
            return redirect(request.url)
        photo = request.files['photo']
        if photo.filename == '':
            return redirect(request.url)
        if photo and allowed_file(photo.filename):
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('add_photos'))

    # Lendo as fotos da pasta de uploads
    photos = os.listdir(app.config['UPLOAD_FOLDER'])
    photos = [f for f in photos if allowed_file(f)]  # Filtra apenas as imagens válidas
    return render_template('add_photos.html', photos=photos)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)
