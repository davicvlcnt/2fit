from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime
import logging
import sys
from flask import abort

app = Flask(__name__, static_folder='static')
app = Flask(__name__)
app.secret_key = 'projeto_integrador'  # Chave secreta para usar flash

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True

DATABASE = 'produtos.db'

def criar_tabela_compras():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            forma_pagamento TEXT NOT NULL,
            endereco_entrega TEXT,
            data_compra DATETIME NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    conn.commit()
    conn.close()

def criar_tabela_receitas():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS receitas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            ingredientes TEXT NOT NULL,
            instrucoes TEXT NOT NULL,
            imagem_url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def criar_tabela_produtos():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT NOT NULL,
            preco REAL NOT NULL,
            imagem_url TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def mostrar_produto_listagem():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    produtos = cursor.fetchall()
    conn.close()
    return render_template('index.html', produtos=produtos)

@app.route('/index_dura')
def renderiza_index_dura():
    return render_template('index_dura.html')

@app.route('/')
def home():
    algum_valor_do_id = 4
    return render_template('home.html')


# Função obter um produto pelo ID
def obter_produto_por_id(produto_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,))
    produto = cursor.fetchone()
    conn.close()
    return produto


@app.route('/adicionar_ao_carrinho/<int:produto_id>')
def adicionar_ao_carrinho(produto_id):
    produto = obter_produto_por_id(produto_id)

    if 'carrinho' not in session:
        session['carrinho'] = []

    session['carrinho'].append({
        'id': produto['id'],
        'nome': produto['nome'],
        'preco': produto['preco']
    })

    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(url_for('mostrar_produto', produto_id=produto_id))

@app.route('/carrinho')
def visualizar_carrinho():
    carrinho = session.get('carrinho', [])
    total = 0

    # Calcula o total e atualiza as informações do produto dentro do carrinho
    for item in carrinho:
        produto = obter_produto_por_id(item['id'])
        item['nome'] = produto['nome']
        item['preco'] = produto['preco']
        total += item['quantidade'] * item['preco']

    return render_template('carrinho.html', carrinho=carrinho, total=total)


@app.route('/remover_do_carrinho/<int:produto_id>')
def remover_do_carrinho(produto_id):
    carrinho = session.get('carrinho', [])

    # Remove o item do carrinho pelo ID do produto
    carrinho = [item for item in carrinho if item['id'] != produto_id]

    # Atualiza a sessão com o novo carrinho
    session['carrinho'] = carrinho

    flash('Produto removido do carrinho!', 'info')
    return redirect(url_for('visualizar_carrinho'))

@app.route('/finalizar_compra', methods=['GET', 'POST'])
def finalizar_compra():
    if request.method == 'POST':
        forma_pagamento = request.form.get('forma_pagamento')
        endereco_entrega = request.form.get('endereco_entrega')
        data_compra = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        carrinho = session.get('carrinho', [])

        # Salva os detalhes da compra no banco de dados
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        for item in carrinho:
            cursor.execute('''
                INSERT INTO compras (produto_id, quantidade, forma_pagamento, endereco_entrega, data_compra)
                VALUES (?, ?, ?, ?, ?)
            ''', (item['id'], item.get('quantidade', 1), forma_pagamento, endereco_entrega, data_compra))
        conn.commit()
        conn.close()

        # Limpa o carrinho após a compra
        session.pop('carrinho', None)

        flash('Compra finalizada com sucesso!', 'success')
        return redirect(url_for('mostrar_produtos'))

    carrinho = session.get('carrinho', [])
    return render_template('finalizar_compra.html', carrinho=carrinho)

@app.route('/receitas')
def mostrar_receitas():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM receitas')
    receitas = cursor.fetchall()
    conn.close()
    return render_template('home.html', receitas=receitas)

@app.route('/receita/<int:receita_id>')
def mostrar_receita(receita_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM receitas WHERE id = ?', (receita_id,))
    receita = cursor.fetchone()
    conn.close()
    return render_template('detalhes_receita.html', receita=receita)

@app.route('/artigos')
def mostrar_artigos():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Lógica de busca e filtragem
    termo_busca = request.args.get('busca', '')
    categoria_filtro = request.args.get('categoria', '')
    tags_filtro = request.args.get('tags', '')

    if termo_busca:
        cursor.execute('SELECT * FROM artigos WHERE titulo LIKE ? OR conteudo LIKE ?',
                       (f'%{termo_busca}%', f'%{termo_busca}%'))
    elif categoria_filtro:
        cursor.execute('SELECT * FROM artigos WHERE categoria = ?', (categoria_filtro,))
    elif tags_filtro:
        cursor.execute('SELECT * FROM artigos WHERE tags LIKE ?', (f'%{tags_filtro}%',))
    else:
        cursor.execute('SELECT * FROM artigos')

    artigos = cursor.fetchall()
    conn.close()
    return render_template('artigos.html', artigos=artigos)

criar_tabela_produtos()
criar_tabela_compras()
criar_tabela_receitas()

if __name__ == '__main__':
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.DEBUG)

    app.logger.debug("Iniciando o aplicativo...")

    try:
        app.run(use_reloader=True, debug=True)
    except Exception as e:
        app.logger.exception("Ocorreu um erro durante a execução do aplicativo:")

    app.logger.debug("Aplicativo encerrado.")

