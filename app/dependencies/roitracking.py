
import cv2, logging, numpy as np
from typing import List, Tuple, Union
from app.dependencies.track import TrackData, Track

logger = logging.getLogger()

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

        # Get list sorted by best levels first
        # Figure out the how much data to process
        max_index = min(self.max_tracks, len(levels))
        sorted_rects, sorted_levels = self.sort(rects, levels, max_index)
        
        rect_list, level_list = ROITracking.transformOverlappingROIS(sorted_rects, sorted_levels, threshold = 1.0)
        if len(rect_list) < len(levels):
            logger.debug(f'before transform:\n{sorted_rects}\n{sorted_levels}')
            logger.debug(f'after transform:\n {rect_list}\n{level_list}')
        
        # Figure out the how much data to process
        max_index = min(self.max_tracks, len(level_list))

        # Get list sorted by best levels first
        #rect_list, level_list = self.sort(transformed_rects, transformed_levels, max_index)

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
        # 3. Overwrite the row and column in the source matrix with -1.0, so it can't be used again 
        
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

    # ------------------------------------------------------------------------

    @staticmethod
    def transformOverlappingROIS (rects: List[List[int]], levels: List[np.float32], threshold: float):
        """
            Assuming the rectangles are provided in level order, 
            return the overlapping rect with the highest level
        """
        
        rect_list = []
        levels_list = []
        combined_indexes = []

        # If the level falls below the threshold, we ignore it's rect and level
        for i in range(len(levels)):
            if levels[i] < threshold:
                combined_indexes.append(i)                

        for i in range (len(levels)):
            is_overlap = False
            for j in range (len(levels)):
                # If the indexes are equal i==j or it's in the combined list ignore
                if i == j or i in combined_indexes or j in combined_indexes:
                    continue
                is_overlap, bigger_rect = ROITracking.doRectanglesOverlap(rects[i], rects[j])
                
                if is_overlap:
                    # Theres an overlap so add the one with the max index (lowest level)
                    # to the combined_list
                    least_rect_index = max(i,j)
                    combined_indexes.append(max(i,j))
                    
                    # if the i index is not the lower value, append it
                    if i != least_rect_index:
                        rect_list.append(rects[i])
                        levels_list.append(levels[i])
                        
                    break

            if not is_overlap and not i in combined_indexes:
                rect_list.append(rects[i])
                levels_list.append(levels[i])


        return (rect_list, levels_list)
    
   



    