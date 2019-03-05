import sys

sys.path.append("../")
import multiprocessing

import Queue


q = Queue.Queue
q.put(item="TESTING")