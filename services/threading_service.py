import threading

class ThreadingService():

    def __init__(self):
        self.wrap_up_threads = threading.Event()

    def wrap_up_threads_now(self):
        self.wrap_up_threads.set()

__threading_service__: ThreadingService = ThreadingService()

def get_threading_service():
    global __threading_service__

    if not __threading_service__:
        __threading_service__ = ThreadingService()
    return __threading_service__
