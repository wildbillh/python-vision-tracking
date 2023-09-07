
import array, cv2, logging, numpy as np
from typing import List, Tuple, Union

logger = logging.getLogger()

class ROITracking:

    def __init__(self, maxTracks: int = 3, historyCount: int = 15):
        """
        """
        self.max_tracks = maxTracks
        self.track_list = np.full((maxTracks, historyCount, 256, 1), -1.0, dtype=np.float32)
        self.levels_track_list = np.zeros((maxTracks, historyCount))


        self.history_count = historyCount
        self.first_run = True
        self.best_track_index = 0
        self.min_correlation_limit = 0.5
        
    # --------------------------------------------------------------------------------------------

    def process (self, processFrame: np.ndarray, rects: List[Tuple[int,int,int,int]], levels: List[float]):
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

        last_stored_histograms = self.getLastStoredHistograms()
        incoming_histograms = self.getIncomingHistograms (processFrame, rect_list)

        correlation_list = self.getCorrelationList (incoming_histograms, last_stored_histograms)
        logger.info(f'correlation list: {correlation_list}')

        # Get the indexes of any tracks that have no data
        empty_tracks_indexes = [i for i in range(self.max_tracks) if last_stored_histograms[i] is None]

        mismatched_incoming_indexes = [i for i in range(object_count) if correlation_list[i] == -1]

        track_indexes_to_write = list(range(self.max_tracks))

        # first write the histograms that have correlations
        for i in range(object_count):
            if correlation_list[i] != -1:               
                self._addTrack(incoming_histograms[i], level_list[i], correlation_list[i])    
                track_indexes_to_write.remove(correlation_list[i])    
                

        # if we have uncorrelated objects and empty tracks, write them
        for mismatch in mismatched_incoming_indexes:
            if len(empty_tracks_indexes) > 0:
                self._addTrack(incoming_histograms[mismatch], level_list[mismatch], empty_tracks_indexes[0]) 
                track_indexes_to_write.remove(empty_tracks_indexes[0])              
                del(empty_tracks_indexes[0])
            else:
                break
        
        # Now write empty hist into any tracks that haven't been written
        for ind in empty_tracks_indexes:
            self._addTrack (None, 0.0, ind)

        track_level_sums = [np.sum(self.levels_track_list[i]) for i in range(self.max_tracks)]
        logger.info(f'level_sums: {track_level_sums}')

        calculated_best = np.argmax(track_level_sums)
        if self.best_track_index != calculated_best:
            logger.info(f'Best track is now {calculated_best}')
            self.best_track_index = calculated_best
          

        return (rect_list, level_list, self.best_track_index)
        
    # -------------------------------------------------------------------
    
    def sort (self, rects: List[Tuple[int,int,int,int]], levels: List[float], maxIndex: int) -> Tuple[List, List]:
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
    
    def _addTrack (self, hist: np.ndarray, level: float, index: int):
        """
            Keep track of the circular buffer. The histogram is of the shape
            (256, 1), 
        """
        # We write the info at the last index of the list and then roll it to the top
        if hist is None:
            self.track_list[index, self.history_count-1] = np.full((256, 1), -1.0, dtype=np.float32)
            self.levels_track_list[index, self.history_count-1] = 0.0
        else:
            self.track_list[index, self.history_count-1] = hist
            self.levels_track_list[index, self.history_count-1] = level

        # Roll the entries we just added at the bottom, to the top
        self.track_list[index] = np.roll(self.track_list[index], shift=1, axis=0)
        self.levels_track_list[index] = np.roll(self.levels_track_list[index], shift=1, axis=0)

    # ------------------------------------------------------------------------------
    
    def getIncomingHistograms (self, frame, rectList):
        """
            Calculates the histograms for the incoming roi's
            Returns a list of size maxTracks
        """
        ret_hist_list = []
        max_index = min(self.max_tracks, len(rectList))
        for i in range(max_index):
            x, y, w, h = rectList[i]
            roi = frame[y:y+h, x:x+w]
            ret_hist_list.append(cv2.calcHist([roi], [0], None, [256], [0,256]))

        return ret_hist_list
    
    # -------------------------------------------------------------------------------
    
    def getLastStoredHistograms (self) -> List[Union[np.ndarray, None]]:
        """
            Query the histogram data and get the latest histogram for each track
            If no histograms, returns None for that entry in the list
        """
        ret_list = []
        for i in range(self.max_tracks):
            val = None
            for j in range(self.history_count):
                val = self.track_list[i,j]
                if val[0][0] > -1.0:
                    break
            ret_list.append(val if val[0][0] > -1 else None)

        return ret_list
    
    # ------------------------------------------------------------------------------------------
    
    def getCorrelationList (self, incomingHistograms: List[np.ndarray], lastStoredHistograms: List[np.ndarray]):
        """
            Returns a list the same size as the incoming rects (max = 3). Each element is either the index of the tracking
            that corresponds or -1
        """
        incoming_len = len(incomingHistograms)
        stored_len = len(lastStoredHistograms)
        
        # Build a 2 dimensional array (incoming X tracks) filled with 0.0
        matrix = np.zeros((incoming_len, stored_len), dtype=np.float32)
        
        # for each object, compare the histograms of each last stored track histogram
        for i in range(incoming_len):
            for j in range(stored_len):
                if lastStoredHistograms[j] is not None:
                    matrix[i,j] = cv2.compareHist(incomingHistograms[i], lastStoredHistograms[j], cv2.HISTCMP_CORREL)

        # Build a single dimension array the size of the incoming histograms to store the index data. 
        # Initialize each value to -1 (unset)
        ret_list = np.full((incoming_len), -1, dtype=np.intp)
        
        # For the number of incoming iterations:
        # 1. Get the max correletion as row,col
        # 2. if above the minimum correlation threshold, set the value at row to col
        # 3. Overwrite the column in the source matrix with -1.0, so it can't be used again 
        for i in range(incoming_len):
            row, col = np.unravel_index(np.argmax(matrix), (incoming_len,stored_len))
            if matrix[row, col] > self.min_correlation_limit:     
                ret_list[row] = col 
            
            matrix[:, col] = np.full((incoming_len), -1)
           

        return ret_list



    