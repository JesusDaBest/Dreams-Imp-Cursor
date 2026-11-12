"""On-demand native Surprise appearances; batch size is not a carousel limit."""
import queue
import threading

class SurpriseCarousel:
    def __init__(self, generate):
        self.generate=generate
        self.items=[]
        self.pending=False
        self.results=queue.Queue()

    def extend(self):
        if self.pending:return
        self.pending=True
        def run():
            try:self.results.put((self.generate(),None))
            except BaseException as exc:self.results.put((None,exc))
        threading.Thread(target=run,daemon=True).start()

    def poll(self):
        try:items,error=self.results.get_nowait()
        except queue.Empty:return False
        self.pending=False
        if error is not None:raise RuntimeError('Native Imp Surprise failed') from error
        known={item['id'] for item in self.items}
        self.items.extend(item for item in items if item['id'] not in known)
        return True

    def ensure_ahead(self, position):
        # Start the next batch while there are still visible choices ahead.
        if position+12>=len(self.items):self.extend()
