from flask import Flask, render_template

app = Flask(__name__)

# Importe a lista de receitas do arquivo receitas.py
from receitas import posts

@app.route('/')
def home():
    algum_valor_do_id = 4
    return render_template('index.html', posts=posts, algum_valor_do_id=algum_valor_do_id)

@app.route('/receita/<int:receita_id>')
def mostrar_receita(receita_id):
    # Obtém a receita com base no receita_id
    receita = next((post for post in posts if post['id'] == receita_id), None)

    if receita:
        return render_template('detalhes_receita.html', receita=receita)
    else:
        return render_template('receita_nao_encontrada.html')

if __name__ == '__main__':
    app.run(debug=True)