import sqlite3

def criar_tabela_e_popular():
    conexao = sqlite3.connect('escola.db')
    cursor = conexao.cursor()

    # Criar a tabela de alunos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            frequencia REAL,
            media_geral REAL,
            media_disciplina REAL,
            atrasos INTEGER,
            ocorrencias INTEGER
        )
    ''')

    # Inserir alguns dados fictícios de exemplo para teste
    alunos_exemplo = [
        ("Ana Silva", 95.0, 8.5, 9.0, 0, 0),
        ("Carlos Souza", 68.5, 4.5, 4.0, 4, 3),
        ("Mariana Oliveira", 88.0, 7.5, 8.0, 1, 1),
        ("Lucas Santos", 65.0, 3.8, 4.2, 5, 6),
        ("Beatriz Costa", 92.0, 9.0, 9.5, 0, 0)
    ]

    # Inserir apenas se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM alunos")
    if cursor.fetchone()[0] == 0:
        cursor.executemany('''
            INSERT INTO alunos (nome, frequencia, media_geral, media_disciplina, atrasos, ocorrencias)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', alunos_exemplo)
        conexao.commit()
        print("Base de dados 'escola.db' criada e populada com sucesso!")
    else:
        print("A base de dados já contém registos.")

    conexao.close()

if __name__ == "__main__":
    criar_tabela_e_popular()