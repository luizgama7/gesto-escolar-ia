from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import joblib
import numpy as np

app = FastAPI(
    title="API de Gestão Escolar com IA",
    description="Módulo de IA integrado com SQLite para apoio à decisão acadêmica."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

modelo = joblib.load('modelo_risco_escolar.pkl')

def conectar_db():
    conn = sqlite3.connect('escola.db')
    conn.row_factory = sqlite3.Row # Permite retornar os resultados como dicionários
    return conn

@app.get("/")
def home():
    return {"status": "API de Gestão Escolar com IA e Banco de Dados online!"}

@app.get("/alunos")
def listar_alunos():
    """Retorna a lista de todos os alunos cadastrados na base de dados."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alunos")
    alunos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return alunos

@app.post("/predict/{aluno_id}")
def prever_risco_aluno(aluno_id: int):
    """Busca um aluno pelo ID no banco de dados e aplica o modelo de IA."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alunos WHERE id = ?", (aluno_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Aluno não encontrado na base de dados.")

    aluno = dict(row)
    
    # Extrair as variáveis para o modelo
    entrada = np.array([[
        aluno['frequencia'],
        aluno['media_geral'],
        aluno['media_disciplina'],
        aluno['atrasos'],
        aluno['ocorrencias']
    ]])
    
    predicao = int(modelo.predict(entrada)[0])
    probabilidade = float(modelo.predict_proba(entrada)[0][predicao])
    status_texto = "Acompanhamento Necessário" if predicao == 1 else "Regular"
    
    return {
        "aluno": aluno['nome'],
        "dados_academicos": aluno,
        "classificacao": predicao,
        "status": status_texto,
        "confianca": round(probabilidade * 100, 2),
        "mensagem": "Resultado destinado ao apoio à decisão humana, sem automação punitiva."
    }