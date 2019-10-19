class ClassMux(object):
	"""
	This multiplexer takes source processors as sources
	"""
	def __init__(self, *sources):
		self.__dict__['sources'] = sources
		self.__dict__['source_num'] = 0

	def __getattr__(self, name):
		if name in self.__dict__:
			return self.__dict__[name]
		else:
			return getattr(self.sources[self.source_num], name)
	
	def __setattr__(self, name, value):
		if name in self.__dict__:
			self.__dict__[name] = value
		else:
			setattr(self.sources[self.source_num], name, value)
