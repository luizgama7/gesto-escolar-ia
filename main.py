import sqlite3
import joblib
import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.ensemble import RandomForestClassifier

app = FastAPI(title="API de Gestão Escolar com IA")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "/tmp/escola_v3.db"
MODEL_PATH = "/tmp/modelo_risco_escolar_v3.pkl"

def carregar_ou_treinar_modelo():
    if os.path.exists(MODEL_PATH):
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            pass
            
    X = [
        [88.5, 7.5, 8.0, 0],
        [58.0, 4.2, 5.0, 2],
        [95.0, 9.0, 9.5, 0],
        [72.0, 5.5, 6.0, 1],
        [45.0, 3.0, 4.0, 3],
        [90.0, 8.5, 8.5, 0],
        [50.0, 3.5, 4.5, 2]
    ]
    y = [0, 1, 0, 0, 1, 0, 1]
    
    clf = RandomForestClassifier(random_state=42)
    clf.fit(X, y)
    joblib.dump(clf, MODEL_PATH)
    return clf

modelo = carregar_ou_treinar_modelo()

def inicializar_banco():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            frequencia REAL NOT NULL,
            nota_mat REAL NOT NULL,
            nota_port REAL NOT NULL,
            historico_reprovacoes INTEGER NOT NULL,
            turma TEXT,
            horario TEXT,
            nome_professor TEXT
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM alunos")
    if cursor.fetchone()[0] == 0:
        alunos_exemplo = [
            ("Ana Silva", 88.5, 7.5, 8.0, 0, "1º Ano A", "Matutino", "Prof. Carlos"),
            ("Bruno Santos", 58.0, 4.2, 5.0, 2, "1º Ano B", "Vespertino", "Profª Mariana"),
            ("Carla Oliveira", 95.0, 9.0, 9.5, 0, "2º Ano A", "Matutino", "Prof. Carlos"),
            ("Daniel Souza", 72.0, 5.5, 6.0, 1, "2º Ano B", "Vespertino", "Profª Mariana"),
            ("Elena Costa", 45.0, 3.0, 4.0, 3, "3º Ano A", "Noturno", "Prof. Roberto")
        ]
        cursor.executemany("""
            INSERT INTO alunos (nome, frequencia, nota_mat, nota_port, historico_reprovacoes, turma, horario, nome_professor)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, alunos_exemplo)
        conn.commit()
    
    conn.close()

inicializar_banco()

def conectar_banco():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

class AlunoCreate(BaseModel):
    nome: str
    frequencia: float
    nota_mat: float
    nota_port: float
    historico_reprovacoes: int
    turma: str
    horario: str
    nome_professor: str

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
    cursor.execute("SELECT id, nome, frequencia, nota_mat, nota_port, historico_reprovacoes, turma, horario, nome_professor FROM alunos")
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
            "historico_reprovacoes": linha["historico_reprovacoes"],
            "turma": linha["turma"],
            "horario": linha["horario"],
            "nome_professor": linha["nome_professor"]
        })
    return alunos

@app.post("/alunos")
def criar_aluno(aluno: AlunoCreate):
    conn = conectar_banco()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO alunos (nome, frequencia, nota_mat, nota_port, historico_reprovacoes, turma, horario, nome_professor)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        aluno.nome, aluno.frequencia, aluno.nota_mat, aluno.nota_port, 
        aluno.historico_reprovacoes, aluno.turma, aluno.horario, aluno.nome_professor
    ))
    conn.commit()
    novo_id = cursor.lastrowid
    conn.close()
    return {"mensagem": "Aluno cadastrado com sucesso!", "id": novo_id}

@app.post("/predict/{aluno_id}")
def prever_risco(aluno_id: int):
    try:
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
            float(aluno["frequencia"]),
            float(aluno["nota_mat"]),
            float(aluno["nota_port"]),
            int(aluno["historico_reprovacoes"])
        ]]
        
        predicao = int(modelo.predict(features)[0])
        probabilidade = float(modelo.predict_proba(features)[0][1])
        
        return {
            "aluno_id": aluno_id,
            "risco_evasao": predicao,
            "probabilidade": probabilidade
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))