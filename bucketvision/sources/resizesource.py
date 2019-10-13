import cv2


class ResizeSource(object):
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
        return cv2.resize(self._base_source.frame, (self.width, self.height))

    @property
    def exposure(self):
        return self._base_source.exposure

    @exposure.setter
    def exposure(self, val):
        self._base_source.exposure = val

    @property
    def new_frame(self):
        return self._base_source.new_frame
