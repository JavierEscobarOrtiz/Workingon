import sys

#Un punto es el mismo directorio y 2 .. es el direcctorio anterior
sys.path.insert(1, '..')
print(sys.path)
print("--------------")
from saludos import Saludo

Saludo()
