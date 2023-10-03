import logging, numpy as np
from typing import List, Tuple, Union


logger = logging.getLogger()

class TrackData:
    """
        Define a simple class to hold track data
    """

    def __init__(self, grayHist: np.ndarray = None, hsvHist: np.ndarray = None, 
                 level: np.float32 = 0.0, rect: np.ndarray = None, pos: Tuple[int,int] = None):
        """
        """
        if grayHist is None:
            self.gray_hist = TrackData.generateEmptyHistogram()
            self.hsv_hist = TrackData.generateEmptyHistogram(isGrayScale=False)
            self.is_empty = True
        else:
            self.gray_hist = grayHist
            self.hsv_hist = hsvHist
            self.is_empty = False

        self.level = level
        self.rect = rect
        self.pos = pos
    
    # -----------------------------------------------------------------------

    def isEmpty(self):
        """
            Determine if the TrackData instance is empty
        """
        return self.is_empty
    
    # ----------------------------------------------------------------------

    def __copy__(self):
        """
        """
        track_data = TrackData (grayHist=self.gray_hist.copy(),
                        hsvHist=self.hsv_hist.copy(),
                        level=np.float32(self.level),
                        pos = tuple(self.pos) if self.pos is not None else None)
        
        track_data.is_empty = self.gray_hist[0][0] == np.float32(-1.0)
        return track_data

    # ----------------------------------------------------------------------

    def __eq__ (self, other):

        if not isinstance(other, self.__class__):
            return False
        
        if other.gray_hist is None or self.gray_hist is None \
            or not np.array_equal(other.gray_hist, self.gray_hist):
            return False
        
        if other.hsv_hist is None or self.hsv_hist is None \
            or not np.array_equal(other.hsv_hist, self.hsv_hist):
            return False
        
        if other.level is None or self.level is None \
            or other.level != self.level:
            return False
        
        if other.pos is None or self.pos is None \
            or other.pos != self.pos:
            return False
        

        return True
    
    # --------------------------------------------------------------------
    
    @staticmethod
    def generateEmptyHistogram (isGrayScale: bool = True):
        
        if isGrayScale:
            return np.full((256, 1), -1.0, dtype=np.float32)
            
        return np.full((180, 256), -1.0, dtype=np.float32)   


# ===========================================================================

class Track:
    """
        Structure of a single track

    """

    def __init__(self, historyCount):
        """
            Fill the Track with empty TrackData
        """
        self.history_count = historyCount
        self.history = np.full((historyCount), TrackData(), dtype=TrackData) 
        self.non_empty_count = 0      

    # ----------------------------------------------------------------------
    
    def getByIndex (self, ind: int) -> TrackData:
        return self.history[ind]
    
    # ------------------------------------------------------------------------

    def addTrack (self, trackData: TrackData = None):
        """
            Keep track of the circular buffer. The histogram is of the shape
            (256, 1), 
        """

        insert_index = self.history_count - 1
        if trackData is None:
            self.history[insert_index] = TrackData()
        else: 
            self.history[insert_index] = trackData  


        # Roll the entries we just added at the bottom, to the top
        self.history = np.roll(self.history, shift=1, axis=0)
          

    # -------------------------------------------------------------

    def getLatestHistogram (self) -> Tuple[int, Union[TrackData, None]]:
        """
            Return the index and value of the last non-empty histogram stored for this
            Track.
            If no histograms stored, return (-1, None)
        """
        ret_val = True
        for i in range (self.history_count):
            
            #if self.history[i] is not None and self.history[i].gray_hist[0][0] >= 0:
            if self.history[i] is not None and not (self.history[i].isEmpty()):
                return (i, self.history[i])   

        # if we get here the track is empty, so return the first TrackData object
        # and TrackData.isEmpty() will be true
        return (-1, None)

    # --------------------------------------------------------------
    
    def isEmpty (self) -> bool:
        """
            Returns true if there are no histograms in the track
        """
        return self.getLatestHistogram()[0] == -1
    
    # --------------------------------------------------------------
    
    def getLevelSums(self) -> np.float32:
        """
            Returns the sum of all of the levels in the track
        """
        return np.sum([self.history[i].level for i in range(self.history_count)])

   