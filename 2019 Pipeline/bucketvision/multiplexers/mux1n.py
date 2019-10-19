class DelegatedSource(object):
	def __init__(self, controller):
		self._controller = controller
		self._new_frame = False

	@property
	def frame(self):
		self._new_frame = False
		return self._controller._base_source.frame

	@property
	def width(self):
		return self._controller._base_source.width

	@property
	def height(self):
		return self._controller._base_source.height

	@property
	def exposure(self):
		return self._controller._base_source.exposure

	@property
	def new_frame(self):
		self._controller.check_new_frame()
		return self._new_frame


class Mux1N:
    """
    This multiplexer takes a series of input sources and creates one
    output source
    """
	def __init__(self, source):
		self._base_source = source
		self._sources = []

	def check_new_frame(self):
		if self._base_source.new_frame:
			self._base_source.new_frame = False
			for source in self._sources:
				source._new_frame = True
	
	def create_output(self):
		source = DelegatedSource(self)
		self._sources.append(source)
		return source
