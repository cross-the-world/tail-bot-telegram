import logging
import threading
from concurrent.futures import ThreadPoolExecutor

thread_number = [-1]
def get_name(nr):
    nr[0] =+ 1
    return "Generated-Thread-{}".format(nr[0])


class BotThreadManager(object):

    def __init__(self, max_workers=4):
        self.futures = []
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Enable logging
        logging.basicConfig(format='%(asctime)s - (%(threadName)-10s) - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
        self.logger = logging.getLogger(__name__)


    def wrap(self, name, func, error, args):
        try:
            self.logger.info("{} starting!!!".format(name))
            result = func(*args)
            self.logger.info("{} finished!!!".format(name))
            return result
        except Exception as err:
            if error:
                error(err)
            self.logger.error("{} failed!!!".format(name))
            self.logger.error(err)
            return None


    def submit(self, name=get_name(thread_number), func=None, args=(), error=None):
        if not func:
            return
        f = self.executor.submit(self.wrap, name, func, error, args)
        self.futures.append(f)
        return f

    def shutdown(self):
        for t in self.futures:
            t.cancel()
        self.executor.shutdown(wait=False)


class CountDownLatch(object):

    def __init__(self, count=1):
        self.count = count
        self.lock = threading.Condition()

    def count_down(self):
        self.lock.acquire()
        self.count -= 1
        if self.count <= 0:
            self.lock.notifyAll()
        self.lock.release()

    def wait(self):
        self.lock.acquire()
        while self.count > 0:
            self.lock.wait()
        self.lock.release()