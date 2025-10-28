import os
if os.path.exists("/mnt"):
 print("this is linux or android")
elif os.path.exists("C:\window") or ("C:\Window"):
 print("this is windows")
else:
 print ("the os isn't recognized")
