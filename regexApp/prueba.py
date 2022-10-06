import time
import os

DATA=os.getenv('DATAFROMK8S')
while True:
    localtime = time.localtime()
    result = time.strftime("%I:%M:%S %p", localtime)
    print(DATA+" - " +result)
    time.sleep(1)
