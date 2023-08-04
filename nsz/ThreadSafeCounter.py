class Counter(object):
	def __init__(self, manager, initval=0):
		self.val = manager.Value('i', initval)
		self.lock = manager.Lock()
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
