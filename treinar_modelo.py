import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib

np.random.seed(42)
num_amostras = 1000

frequencia = np.random.uniform(50.0, 100.0, num_amostras)
media_geral = np.random.uniform(2.0, 10.0, num_amostras)
media_disciplina = np.random.uniform(2.0, 10.0, num_amostras)
atrasos = np.random.randint(0, 15, num_amostras)
ocorrencias = np.random.randint(0, 8, num_amostras)

classe = []
for i in range(num_amostras):
    if frequencia[i] < 75.0 or media_geral[i] < 5.5 or ocorrencias[i] >= 4:
        classe.append(1)
    else:
        classe.append(0)

df = pd.DataFrame({
    'frequencia': frequencia,
    'media_geral': media_geral,
    'media_disciplina': media_disciplina,
    'atrasos': atrasos,
    'ocorrencias': ocorrencias,
    'classe': classe
})

X = df[['frequencia', 'media_geral', 'media_disciplina', 'atrasos', 'ocorrencias']]
y = df['classe']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

modelo = RandomForestClassifier(n_estimators=100, random_state=42)
modelo.fit(X_train, y_train)

y_pred = modelo.predict(X_test)
print("=== Relatório de Classificação ===")
print(classification_report(y_test, y_pred))

print("=== Matriz de Confusão ===")
print(confusion_matrix(y_test, y_pred))

joblib.dump(modelo, 'modelo_risco_escolar.pkl')
print("\nModelo salvo com sucesso em 'modelo_risco_escolar.pkl'!")
