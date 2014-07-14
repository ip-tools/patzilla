# https://github.com/unbit/uwsgi/blob/master/uwsgidecorators.py
try:
    import uwsgi
except ImportError:
    uwsgi = None

postfork_chain = []

def postfork_chain_hook():
    for f in postfork_chain:
        f()

if uwsgi:
    uwsgi.post_fork_hook = postfork_chain_hook

class postfork(object):
    def __init__(self, f):
        if callable(f):
            self.wid = 0
            self.f = f
        else:
            self.f = None
            self.wid = f
        postfork_chain.append(self)
    def __call__(self, *args, **kwargs):
        if self.f:
            if self.wid > 0 and self.wid != uwsgi.worker_id():
                return
            return self.f()
        self.f = args[0]
