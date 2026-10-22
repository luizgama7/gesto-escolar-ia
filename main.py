import sqlite3
import joblib
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="API de Gestão Escolar com IA")

# Configurar CORS para permitir acessos livres à API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Carregar o modelo preditivo treinado (.pkl)
try:
    modelo = joblib.load("modelo_risco_escolar.pkl")
except Exception as e:
    modelo = None

def inicializar_banco():
    """Cria a base de dados e a tabela de alunos automaticamente se não existirem"""
    conn = sqlite3.connect("escola.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            frequencia REAL NOT NULL,
            nota_mat REAL NOT NULL,
            nota_port REAL NOT NULL,
            historico_reprovacoes INTEGER NOT NULL
        )
    ''')
    
    # Inserir dados de exemplo caso a tabela esteja vazia
    cursor.execute("SELECT COUNT(*) FROM alunos")
    if cursor.fetchone()[0] == 0:
        alunos_exemplo = [
            ("Ana Silva", 88.5, 7.5, 8.0, 0),
            ("Bruno Santos", 58.0, 4.2, 5.0, 2),
            ("Carla Oliveira", 95.0, 9.0, 9.5, 0),
            ("Daniel Souza", 72.0, 5.5, 6.0, 1),
            ("Elena Costa", 45.0, 3.0, 4.0, 3)
        ]
        cursor.executemany("""
            INSERT INTO alunos (nome, frequencia, nota_mat, nota_port, historico_reprovacoes)
            VALUES (?, ?, ?, ?, ?)
        """, alunos_exemplo)
        conn.commit()
    
    conn.close()

# Executar a inicialização ao iniciar a aplicação
inicializar_banco()

def conectar_banco():
    conn = sqlite3.connect("escola.db")
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
def home():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "<html><body><h3>API de Gestão Escolar com IA e Banco de Dados online!</h3></body></html>"

@app.get("/alunos")
def listar_alunos():
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, frequencia, nota_mat, nota_port, historico_reprovacoes FROM alunos")
    linhas = cursor.fetchall()
    conn.close()
    
    alunos = []
    for linha in linhas:
        alunos.append({
            "id": linha["id"],
            "nome": linha["nome"],
            "frequencia": linha["frequencia"],
            "nota_mat": linha["nota_mat"],
            "nota_port": linha["nota_port"],
            "historico_reprovacoes": linha["historico_reprovacoes"]
        })
    return alunos

@app.post("/predict/{aluno_id}")
def prever_risco(aluno_id: int):
    if modelo is None:
        raise HTTPException(status_code=500, detail="Modelo de IA não carregado no servidor.")
        
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("SELECT frequencia, nota_mat, nota_port, historico_reprovacoes FROM alunos WHERE id = ?", (aluno_id,))
    aluno = cursor.fetchone()
    conn.close()
    
    if not aluno:
        raise HTTPException(status_code=404, detail="Aluno não encontrado.")
        
    features = [[
        aluno["frequencia"],
        aluno["nota_mat"],
        aluno["nota_port"],
        aluno["historico_reprovacoes"]
    ]]
    
    predicao = int(modelo.predict(features)[0])
    probabilidade = float(modelo.predict_proba(features)[0][1])
    
    return {
        "aluno_id": aluno_id,
        "risco_evasao": predicao,
        "probabilidade": probabilidade
    }