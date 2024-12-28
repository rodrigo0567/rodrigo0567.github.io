from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

confirmed_guests = []

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/validate_answer', methods=['POST'])
def validate_answer():
    answer = request.form.get('answer')
    if answer == 'Preto':  # Resposta correta
        return redirect(url_for('main'))
    # Resposta incorreta, redireciona com o parâmetro de erro
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
        # Adiciona o nome à lista de convidados confirmados
        confirmed_guests.append(name)
        
        # Abre o arquivo guest.txt em modo de acréscimo ('a')
        with open('guest.txt', 'a') as file:
            file.write(name + '\n')  # Adiciona o nome no arquivo com uma nova linha
        
    return redirect(url_for('main'))


if __name__ == '__main__':
    app.run(debug=True)
