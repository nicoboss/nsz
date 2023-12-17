from multiprocessing import Value, Lock

class Counter(object):
	def __init__(self, manager, initval=0):
		self.val = Value('i', initval)
		self.lock = Lock()
	def set(self, newValue):
		with self.lock:
			self.val.value = newValue
	def increment(self):
		with self.lock:
			self.val.value += 1
	def decrement(self):
		with self.lock:
			self.val.value -= 1
	def value(self):
		with self.lock:
			return self.val.value
