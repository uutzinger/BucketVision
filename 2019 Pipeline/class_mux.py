

class Class_Mux(object):
	def __init__(self, *sources):
		self.sources = sources
		self.source_num = 0

	def __getattr__(self, name):
		return getattr(self.sources[self.source_num], name)
