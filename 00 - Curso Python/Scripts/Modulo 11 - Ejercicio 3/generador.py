import random
import math

def leer_numero(ini, fin, mensaje):

	while True:
		try:
			valor = int( input(mensaje) )
		except:
			print("Error, numero no valido")
		else:
			if valor >= ini and valor <= fin:
				break
				
	return valor
	

def generador():
	numeros = leer_numero(1,20,"Cuantos numeros quieres generar? [1-20]")
	modo = leer_numero(1,3,"Como quieres redondear los numeros? [1]Al alza [2]A la baja [3]Normal")
	
	l = []
	for i in range(numeros):
		n = random.uniform(0,101)
		if modo == 1:
			n1 = math.ceil(n)
		elif modo == 2:
			n1 = math.floor(n)
		else:
			n1 = round(n)
			
		print("{} se ha redondeado a {}".format(n,n1))
		l.append(n1)

	print(l)
	
generador()