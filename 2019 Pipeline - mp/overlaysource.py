from cv2 import line

class OverlaySource(object):
    def __init__(self, base_source, res=None):
        self._base_source = base_source
        if res is not None:
            self.width = res[0]
            self.height = res[1]
        else:
            self.width = int(self._base_source.width)
            self.height = int(self._base_source.height)

    @property
    def frame(self):
        return line(self._base_source.frame, (self.width//2, self.height), (self.width//2, 0), (0, 255, 0), 2)

    @property
    def exposure(self):
        return self._base_source.exposure

    @exposure.setter
    def exposure(self, val):
        self._base_source.exposure = val

    @property
    def width(self):
        return self._base_source.width

    @width.setter
    def width(self, val):
        self._base_source.width = val

    @property
    def height(self):
        return self._base_source.height

    @height.setter
    def height(self, val):
        self._base_source.height = val

    @property
    def new_frame(self):
        return self._base_source.new_frame
