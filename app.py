from flask import Flask, render_template, request, redirect, url_for,session
import random
import gspread
from google.oauth2.service_account import Credentials
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv

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


creds = Credentials.from_service_account_file(
    'convite-446020-4f64e2aab3d5.json',
    scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
)

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

@app.route('/add_music', methods=['GET', 'POST'])
def add_music():
    if request.method == 'POST':
        music_name = request.form['music']
        
        # Verifica se o usuário tem token válido
        if 'token_info' in session:
            try:
                # Obtém o token da sessão
                token_info = session['token_info']
                sp = spotipy.Spotify(auth=token_info['access_token'])  # Cria a instância do cliente Spotify com o token

                results = sp.search(q=music_name, type='track', limit=1)
                if results['tracks']['items']:
                    track_uri = results['tracks']['items'][0]['uri']
                    playlist_id = os.getenv('PLAYLIST_ID')
                    sp.playlist_add_items(playlist_id, [track_uri])
                    # Redireciona para /add_music com status de sucesso
                    return redirect(url_for('add_music', status='success'))
                else:
                    # Se a música não for encontrada, redireciona com status de erro
                    return redirect(url_for('add_music', status='error'))
            except Exception as e:
                print(f"Erro: {e}")
                return f"Ocorreu um erro: {e}"
        else:
            return redirect(url_for('add_music', status='error'))
    else:
        # Renderiza o formulário e passa o status para o template
        return render_template('add_music.html', status=request.args.get('status'))

    
@app.route('/callback')
def callback():
    # Recupera o código de autorização do Spotify
    token_info = sp.auth_manager.get_access_token(request.args['code'])
    session['token_info'] = token_info  # Armazena o token na sessão
    return redirect(url_for('add_music'))



@app.route('/login')
def login():
    # A URL de redirecionamento do Spotify será definida aqui
    auth_url = sp.auth_manager.get_authorize_url()
    return redirect(auth_url)

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
