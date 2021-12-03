import os
import time
import datetime

reloj = datetime.datetime.now()
dt = datetime.timedelta(seconds=1)

while True:
	os.system('cls')
	print("{}:{}:{}".format(reloj.hour,reloj.minute,reloj.second) )
	reloj = reloj + dt
	time.sleep(1)
	
	
