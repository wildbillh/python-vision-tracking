
import cv2, logging, numpy as np
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

        # Get list sorted by best levels first
        rect_list, level_list = self.sort(rects, levels)

        object_count = len(levels)

        # Figure out the how much data to process
        max_index = min(self.max_tracks, object_count)
        logger.info(f'process called levels: {level_list}')


        last_stored_histograms = self.getLastStoredHistograms()
        #logger.info(f'last_stored: {last_stored_histograms}')
        incoming_histograms = self.getIncomingHistograms (processFrame, rect_list)

        correlation_list = self.getCorrelationList (incoming_histograms, last_stored_histograms)


        #logger.info(f'correlation: {correlation_list}')

        empty_tracks_indexes = [i for i in range(self.max_tracks) if last_stored_histograms[i] is None]
        mismatched_incoming_indexes = [i for i in range(object_count) if correlation_list[i] is None]

        logger.info(f'empty_tracks: {empty_tracks_indexes}, mismatched: {mismatched_incoming_indexes}')
        track_indexes_to_write = list(range(self.max_tracks))
        logger.info(f'track_indexes_to_write: {track_indexes_to_write}')

        logger.info(f'correlation_list: {correlation_list}')

        # first write the histograms that have correlations
        for i in range(object_count):
            if correlation_list[i] is not None:
                logger.info(f'adding incoming: {i} to track {correlation_list[i]}')
                self._addTrack(incoming_histograms[i], level_list[i], correlation_list[i])  
                logger.info(f'track_indexes_to_write: {track_indexes_to_write}')
                track_indexes_to_write.remove(correlation_list[i])    
                logger.info(f'track_indexes_to_write: {track_indexes_to_write}')

        # if we have uncorrelated objects and empty tracks, write them
        for mismatch in mismatched_incoming_indexes:
            if len(empty_tracks_indexes) > 0:
                logger.info(f'incoming no match: {mismatch} to empty track: {empty_tracks_indexes[0]}')
                self._addTrack(incoming_histograms[mismatch], level_list[mismatch], empty_tracks_indexes[0]) 
                track_indexes_to_write.remove(empty_tracks_indexes[0]) 
                logger.info(f'Write incoming: {mismatch} to track: {empty_tracks_indexes[0]}')
                del(empty_tracks_indexes[0])
            else:
                break
        
        # Now write empty hist into any tracks that haven't been written
        for ind in empty_tracks_indexes:
            self._addTrack (None, 0.0, ind)
            logger.info(f'Write empty hist to {ind}')   

        return (rect_list, level_list)
        
    # -------------------------------------------------------------------
    
    def sort (self, rects: List[Tuple[int,int,int,int]], levels: List[float]) -> Tuple[List, List]:
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
        
        return (ret_rects, ret_levels) 
    
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

        self.track_list[index] = np.roll(self.track_list[index], shift=1, axis=0)
        self.levels_track_list[index] = np.roll(self.levels_track_list[index], shift=1, axis=0)

    # ------------------------------------------------------------------------------
    
    def getIncomingHistograms (self, frame, rectList):
        """
            Calculates the histograms for the incoming roi's
            Returns a list of size 1 - maxTracks
        """
        ret_hist_list = []
        max_index = min(3, len(rectList))
        for i in range(max_index):
            x, y, w, h = rectList[i]
            roi = frame[y:y+h, x:x+w]
            ret_hist_list.append(cv2.calcHist([roi], [0], None, [256], [0,256]))

        return ret_hist_list
    
    # -------------------------------------------------------------------------------
    
    def getLastStoredHistograms (self) -> List[Union[np.ndarray, None]]:
        """
            Query the histogram data and get the latest histogram for each track
            If no histograms returns None for that entry in the list
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
    
    def getCorrelationList (self, incomingHistograms: List[np.ndarray], lastStoredHistograms: List[Union[np.ndarray, None]]):
        """
            Returns a list the same size as the incoming rects (max = 3). Each element is either the index of the tracking
            that corresponds or none 
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


        ret_list = []
        logger.info(matrix)
        
        for i in range(incoming_len):
            max_index = np.argmax(matrix[i])
            ret_list.append(max_index if matrix[i,max_index] > 0.5 else None)
            np.delete(matrix, obj=max_index, axis=1)

        return ret_list



    