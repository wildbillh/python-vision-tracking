
import array, cv2, logging, numpy as np
from typing import List, Tuple, Union


logger = logging.getLogger()

class TrackData:
    """
        Define a simple class to hold track data
    """

    def __init__(self, grayHist: np.ndarray = None, hsvHist: np.ndarray = None, 
                 level: np.float32 = 0.0, pos: Tuple[int,int] = None):
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

# =========================================================================    

class ROITracking:

    def __init__(self, maxTracks: int = 3, historyCount: int = 15):
        """
        """
        self.max_tracks = maxTracks
        self.history_count = historyCount
        self.first_run = True
        self.best_track_index = 0
        self.min_correlation_limit = 0.5

        # Get the list of tracks
        self.tracks = [Track(self.history_count) for i in range (self.max_tracks)]
        
    # --------------------------------------------------------------------------------------------
    
    def process (self, processFrame: np.ndarray, hsvFrame: np.ndarray, rects: List[Tuple[int,int,int,int]], levels: List[float]):
        """
            Given the process frame, list of roi dims and levels. Build correlation histograms from the 
            best three roi's and store them in a circular buffer.
        """

        # Figure out the how much data to process
        max_index = min(self.max_tracks, len(levels))

        # Get list sorted by best levels first
        rect_list, level_list = self.sort(rects, levels, max_index)

        object_count = len(level_list)

        logger.info(f'process called levels: {level_list}')


        last_stored_histograms: List[TrackData] = self.getLatestHistograms()
        logger.info(f'last_stored_hist len: {len(last_stored_histograms)}')
        incoming_histograms: List[TrackData] = self.calculateIncomingHistograms (
            grayFrame=processFrame, 
            hsvFrame=hsvFrame,
            rectList=rect_list)
        

        correlation_list = self.getCorrelationList (incomingTracks = incoming_histograms,
                                                    lastStoredTracks = last_stored_histograms,
                                                    )
        
        logger.info(f'correlation list: {correlation_list}')

        # Get the indexes of any tracks that have no data
        empty_tracks_indexes = [i for i in range(self.max_tracks) if last_stored_histograms[i] is None]

        # Get the indexes where there is no correlation to existing trackes
        mismatched_incoming_indexes = [i for i in range(object_count) if correlation_list[i] == -1]

        track_indexes_to_write = list(range(self.max_tracks))

        # first write the histograms that have correlations
        for i in range(object_count):
            if correlation_list[i] != -1:
                track_data = TrackData(grayHist=incoming_histograms[i].gray_hist,
                                       hsvHist=incoming_histograms[i].hsv_hist,
                                       level=level_list[i])               
               
                self.addTrack(trackData=track_data, index=correlation_list[i])
                track_indexes_to_write.remove(correlation_list[i])    
                

        # if we have uncorrelated objects and empty tracks, write them
        for mismatch in mismatched_incoming_indexes:
            if len(empty_tracks_indexes) > 0:
                track_data = TrackData(grayHist=incoming_histograms[mismatch].gray_hist,
                                       hsvHist=incoming_histograms[mismatch].hsv_hist,
                                      level=level_list[mismatch])
                self.addTrack(track_data, empty_tracks_indexes[0]) 
                track_indexes_to_write.remove(empty_tracks_indexes[0])              
                del(empty_tracks_indexes[0])
            else:
                break
        
        # Now write empty hist into any tracks that haven't been written
        for ind in empty_tracks_indexes:
            self.addTrack (TrackData(), ind)

        #track_level_sums = [np.sum(self.levels_track_list[i]) for i in range(self.max_tracks)]
        track_level_sums = [self.tracks[i].getLevelSums() for i in range(self.max_tracks)]
        logger.info(f'level_sums: {track_level_sums}')

        calculated_best = np.argmax(track_level_sums)
        if self.best_track_index != calculated_best:
            logger.info(f'Best track is now {calculated_best}')
            self.best_track_index = calculated_best
          

        return (rect_list, level_list, correlation_list, self.best_track_index)
        
    # -------------------------------------------------------------------
    
    def sort (self, rects: List[Tuple[int,int,int,int]], levels: List[float], maxIndex: int) -> Tuple[np.ndarray, np.ndarray]:
        """
            Sort both the rects and levels based on the levels values
        """  

        ret_rects = []
        ret_levels = []
        # Get the list of indexes of the levels sorted ascending
        sorted_indexes = np.argsort(levels, 0)
        # Store the values in descending order
        for i in range(len(rects) - 1, -1, -1):
            ret_rects.append(rects[sorted_indexes[i]])
            ret_levels.append(levels[sorted_indexes[i]])
        
        return (np.array(ret_rects)[0:maxIndex], np.array(ret_levels)[0:maxIndex]) 
    
    # -------------------------------------------------------------------
    
    def addTrack (self, trackData: TrackData, index: int):
        """
            Keep track of the circular buffer. The histogram is of the shape
            (256, 1), 
        """

        self.tracks[index].addTrack(trackData = trackData)      

    # ------------------------------------------------------------------------------
    
    def calculateIncomingHistograms (self, 
                                     grayFrame: np.ndarray, 
                                     hsvFrame: np.ndarray, 
                                     rectList: List[Tuple[int,int,int,int]]) -> List[TrackData]:
        """
            Calculates the gray and hsv histograms for the incoming roi's
            Returns a list of TrackData
        """
        max_index = min(self.max_tracks, len(rectList))
        hist_list = []
        
        for i in range(max_index):
            x, y, w, h = rectList[i]
            gray_roi = grayFrame[y:y+h, x:x+w]
            hsv_roi = hsvFrame[y:y+h, x:x+w]

            # Calculate the hsv hist and normalize
            hsv_hist = cv2.calcHist([hsv_roi], [0,1], None, [180,256], [0, 180, 0, 256])
            hsv_hist = cv2.normalize(hsv_hist, hsv_hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)

            # Append a TrackData class to the return list
            hist_list.append(TrackData(
                grayHist=cv2.calcHist([gray_roi], [0], None, [256], [0,256]),
                hsvHist=hsv_hist))
            
        return hist_list
    
    
    # -------------------------------------------------------------------------------
    
    def getLatestHistograms (self) -> List[Union[TrackData, None]]:
        """
            Query the histogram data and get the latest histogram for each track
            If no histograms, returns None for that entry in the list
        """
        ret_list = []
        for i in range(self.max_tracks):
            
            ind, track_data = self.tracks[i].getLatestHistogram()
            ret_list.append(track_data if ind >= 0 else None)
        
        return ret_list


     # ------------------------------------------------------------------------------------------
    
    def getCorrelationList (self, incomingTracks: List[TrackData],                            
                            lastStoredTracks: List[TrackData]):
        """
            Returns a list the same size as the incoming rects (max = 3). Each element is either the index of the tracking
            that corresponds or -1
        """

        incoming_len = len(incomingTracks)
        stored_len = len(lastStoredTracks)
        
        # Build a 2 dimensional array (incoming X tracks) filled with 0.0
        matrix = np.zeros((incoming_len, stored_len), dtype=np.float32)
        
        # for each object, compare the histograms of each last stored track histogram
        for i in range(incoming_len):
            for j in range(stored_len):
                if lastStoredTracks[j] is not None and not lastStoredTracks[j].isEmpty():
                    gray_corr = cv2.compareHist(incomingTracks[i].gray_hist, lastStoredTracks[j].gray_hist, cv2.HISTCMP_CORREL)
                    hsv_corr = cv2.compareHist(incomingTracks[i].hsv_hist, lastStoredTracks[j].hsv_hist, cv2.HISTCMP_CORREL)
                    combined_corr = gray_corr + hsv_corr
                    #print(i, j, gray_corr, hsv_corr, combined_corr, flush=True)
                    matrix[i,j] = combined_corr

        # Build a single dimension array the size of the incoming histograms to store the index data. 
        # Initialize each value to -1 (unset)
        ret_list = np.full((incoming_len), -1, dtype=np.intp)
        
        # For the number of incoming iterations:
        # 1. Get the max correletion as row,col
        # 2. if above the minimum correlation threshold, set the value at row to col
        # 3. Overwrite the column in the source matrix with -1.0, so it can't be used again 
        
        print(matrix, flush=True)
        for i in range(incoming_len):
            row, col = np.unravel_index(np.argmax(matrix), (incoming_len,stored_len))
            print("row/col", row, col, flush=True)
            if matrix[row, col] > self.min_correlation_limit:     
                ret_list[row] = col 
            print("ret_list", ret_list, flush=True)
            matrix[:, col] = np.full((incoming_len), -1) 
            matrix[row, :] = np.full((stored_len), -1) 

            print(matrix, flush=True)        

        return ret_list    
    
    # ----------------------------------------------------------------------------------------
    @staticmethod
    def doRectanglesOverlap(rect1: Tuple[int, int, int, int], rect2: Tuple[int, int, int, int]):
        """
            When given 2 rectangles in the format (x1, y1, w, h), deterimine if the 2 rectangles overlap 
        """

        # convert into x and y coords
        r1x1 = rect1[0]
        r1y1 = rect1[1]
        r1x2 = r1x1 + rect1[2]
        r1y2 = r1y1 + rect1[3]

        r2x1 = rect2[0]
        r2y1 = rect2[1]
        r2x2 = r2x1 + rect2[2]
        r2y2 = r2y1 + rect2[3]
   
        # If one of the rectangles is to the the left of the other
        if r1x1 > r2x2 or r2x1 > r1x2:
            return False, None
 
        #If one rectangle is above other
        if r1y1 > r2y2 or r2y1 > r1y2:
            return False, None
    
        # if either rectangle has no area return False
        if r1x1 == r1x2 or r1y1 == r1y2 or r2x1 == r2x2 or r2y1 == r2y2:
            return False, None
 
        # Find the bigger of the two
        if ((r1x2 - r1x1) * (r1y2 - r1y1)) > ((r2x2 - r2x1) * (r2y2 - r2y1)):
            return (True, rect1)
    
        return (True, rect2)

    @staticmethod
    def transformOverlappingROIS (rects, levels, threshold: float):
        """
        """
        rect_list = []
        levels_list = []
        combined_indexes = []

        # If the level falls below the threshold, we ignore it's rect and level
        for i in range(len(levels)):
            if levels[i] < threshold:
                combined_indexes.append(i)           

        rect_tuple = None

        for i in range (len(levels)):
            is_overlap = False
            for j in range (len(levels)):
                if i == j or i in combined_indexes or j in combined_indexes:
                    continue
                is_overlap, bigger_rect = ROITracking.doRectanglesOverlap(rects[i], rects[j])
                if is_overlap:
                    rect_list.append(bigger_rect)
                    levels_list.append(levels[i] + levels[j])
                    combined_indexes.append(i)
                    combined_indexes.append(j)
                    break
            if not is_overlap and not i in combined_indexes:
                rect_list.append(rects[i])
                levels_list.append(levels[i])


        return (rect_list, levels_list)
    
   



    