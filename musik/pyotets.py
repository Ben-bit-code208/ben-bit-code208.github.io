from pyo import Server

print("creating server...")
try:
    s = Server()
    s.boot()
    print("boot")
    s.start()
    print("started")
    s.stop()
    print("stopped")
    s.shutdown()
    print("shutdown")
finally:
    print("done")
    exit(0x0)