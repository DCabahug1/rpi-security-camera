import threading
import time

finished = False

def counter():
  count = 0

  while not finished:
      time.sleep(1)
      count += 1
      print(count)


threading.Thread(target=counter).start()

user_input = None

while (user_input != '0' and not finished):
  user_input = input("Type 'end' to end program\n")
  finished = True
  
