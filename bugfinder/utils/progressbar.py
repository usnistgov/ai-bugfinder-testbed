from multiprocessing import Queue
from math import floor, log10
from progress.bar import Bar
from time import sleep

class SlowBar(Bar):

    # New suffix with ETA
    suffix = '%(percent).1f%% - ETA %(slow_eta)s '

    # Utility function to properly display the ETA
    @property
    def slow_eta(self):
        return str(self.eta_td).split('.')[0]

    def extend(self, val):
        self.max += val

class BestBar(SlowBar):

    b_val = float("nan")
    b_age = 0
    b_stats = {}

    # New suffix with ETA
    suffix = '%(percent).1f%% - ETA %(slow_eta)s - Best: %(best_val)+.fx (age: %(best_age)d stats: %(best_stats)s)'

    # Utility function to properly display the ETA
    @property
    def best_val(self):
        return float('%.3g' % (self.b_val - 1.))

    @property
    def best_age(self):
        return self.b_age

    @property
    def best_stats(self):
        stats = sorted(self.b_stats.items(), key=lambda x:x[1], reverse=True)
        return ", ".join(["%d=%d" % stats[0], "%d=%d" % stats[1], "others=%d" % sum(s[1] for s in stats[2:])]) if len(stats) > 1 else "n/a"

    def next(self, n=1, best=None, age=None):
        if best is not None:
            if self.b_age in self.b_stats:
                self.b_stats[self.b_age] += 1
            else:
                self.b_stats[self.b_age] = 1
            self.b_val = best
            self.b_age = 0
        elif age is not None:
            self.b_age = age
        super(BestBar, self).next(n=n)

class MultiBar(SlowBar):

    jobs, done = 0, 0
    queue = Queue()
    suffix = '%(percent).1f%% - ETA %(slow_eta)s - jobs %(jobz)s '

    @property
    def jobz(self):
        return "%d/%d" % (self.done, self.jobs)

    def subscribe(self, max):
        self.queue.put({"extend": max})
    
    def unsubscribe(self):
        self.queue.put({"done": None})

    def next(self, n=1):
        self.queue.put({"consume": n})

    def refresh(self):
        while self.jobs == 0 or self.done < self.jobs or not self.queue.empty():
            steps = 0
            while not self.queue.empty():
                op, val = list(self.queue.get().items())[0]
                if op == "consume":
                    steps += val
                elif op == "extend":
                    self.extend(val)
                    self.jobs += 1
                elif op == "done":
                    self.done += 1
            super(MultiBar, self).next(n=steps)
            sleep(.1)
