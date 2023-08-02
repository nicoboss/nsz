from multiprocessing import Manager

class Counter(object):
	def __init__(self, manager, initval=0):
		self.val = manager.Value('i', initval)
	def set(self, newValue):
		self.val.value = newValue
	def increment(self):
		self.val.value += 1
	def decrement(self):
		self.val.value -= 1
	def value(self):
		return self.val.value
