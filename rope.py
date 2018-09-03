import cv2

class Rope:
    """
    An OpenCV pipeline created to find faces
    """
    
    def __init__(self):
        """initializes all values to presets or None if need to be set
        """
     

    def process(self, source0):
        """
        Runs the pipeline and sets all outputs to new values.
        """
        
        # Draw reticle for rope guide
        color = (0,255,0)
        thickness = 2

        s = source0.shape
        hi = 0
        wi = 1

        pt1 = (40,240)
        pt2 = (150,100)
        cv2.line(source0,pt1,pt2,color,thickness,cv2.LINE_AA)
        
        pt1 = (280,240)
        pt2 = (170,100)
        
        cv2.line(source0,pt1,pt2,color,thickness,cv2.LINE_AA)
        