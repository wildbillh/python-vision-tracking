
import array, copy, numpy as np, unittest
from app.dependencies.roitracking import TrackData, Track, ROITracking

class TrackDataTest (unittest.TestCase):

    def test_constructor(self):

        # Test the empty track
        trackData = TrackData()
        self.assertTrue(trackData.isEmpty())
        self.assertEqual(trackData.gray_hist.all(), TrackData.generateEmptyHistogram().all())
        self.assertEqual(trackData.hsv_hist.all(), TrackData.generateEmptyHistogram(isGrayScale=False).all())
        self.assertEqual(trackData.level, np.float32(0.0))
        self.assertIsNone(trackData.pos)



class TrackTest (unittest.TestCase):

    def test_constructor (self):

        track = Track(historyCount=15)
        self.assertEqual(len(track.history), 15)
        first_track: TrackData = track.history[0]
        self.assertEqual(first_track.gray_hist.shape, (256, 1))
        self.assertEqual(first_track.hsv_hist.shape, (180, 256))
        self.assertEqual(first_track.level, np.float32(0.0))
        self.assertIsNone(first_track.pos)
        
    
    # -----------------------------------------------------------------
    
    def test_add_tracks (self):

        gray_hist_1 = np.full((256, 1), 4.0, dtype=np.float32)
        gray_hist_2 = np.full((256, 1), 8.0, dtype=np.float32)

        hsv_hist_1 = np.full((180, 256), 4.0, dtype=np.float32)
        hsv_hist_2 = np.full((180, 256), 8.0, dtype=np.float32)

        # Create track record and test that it's empty
        track = Track(historyCount=2) 
        self.assertTrue(track.isEmpty()) 

        data1 = TrackData(grayHist=gray_hist_1, hsvHist=hsv_hist_1, 
                                 level=np.float32(3.45), pos=(0,0))
        
        # Add a non empty hist and level and test
        track.addTrack(copy.copy(data1))
        track_item: TrackData = track.getByIndex(0) 
        self.assertEqual(track_item, data1)  
        
        
        # Add an empty track and test 
        track.addTrack(TrackData())
        track_item: TrackData = track.getByIndex(0) 
        self.assertTrue(track_item.isEmpty())
        
        # Test that the latest histogram returned is index 1
        self.assertEqual(track.getLatestHistogram()[0], 1)
        
        # Add a nonempty record
        data2 = TrackData(grayHist=gray_hist_2, hsvHist=hsv_hist_2, level=8.0, pos=(1,1))
        track.addTrack (copy.copy(data2))

        # Now the first record should be 8.0's and the second record shoud be empty
        track_item = track.getByIndex(0)
        self.assertEqual(track_item, data2)
        self.assertEqual(track.getLatestHistogram()[0], 0)

        track_item = track.getByIndex(1)
        self.assertTrue(track_item.isEmpty())
        
        
# ===============================================================================

class ROITrackingTest (unittest.TestCase):
    
    def test_constructor(self):

        roi = ROITracking(maxTracks=3, historyCount=15)

        self.assertEqual(roi.max_tracks, 3)
        self.assertEqual(roi.history_count, 15)
        self.assertTrue(roi.first_run)
        self.assertEqual(len(roi.tracks), 3)

     
    # --------------------------------------------------------------
    
    def test_get_latest_histograms (self):

        roi = ROITracking(maxTracks=3, historyCount=15)
        # Since all of the tracks are empty, getLatestHistograms should 
        # return a list of (-1, None) tuples
        latest_list = roi.getLatestHistograms()
        self.assertEqual(latest_list, [None,None,None])
        
        # Add values to track 0
        level = np.float32(4.0)
        hist_data = np.full((256,1), 4.0, dtype=np.float32)
        hsv_data = np.full((180, 256), 4.0, dtype=np.float32)
        roi.addTrack(TrackData(grayHist=hist_data, hsvHist=hsv_data, level=level, pos=(2,2)), index=0)

        # Test to see if the latest list is the one you just added
        latest_list = roi.getLatestHistograms()
        
        #self.assertEqual(latest_list[0].all(), hist_data.all())

    # -----------------------------------------------------------------------------

    def test_sort (self):
        """
            Test the sorting function
        """

        rects_list = [(1,1,1,1), (2,2,2,2), (3,3,3,3)]
        level_list = [2.01, 4.0, 3.02]

        exp_rects_list = np.array([[2, 2, 2, 2],[3, 3, 3, 3],[1, 1, 1, 1]])
        exp_level_list = np.array([4.0, 3.02, 2.01])

        roi = ROITracking(maxTracks=3, historyCount=15)
        sorted_rects, sorted_levels = roi.sort(rects=rects_list, levels=level_list, maxIndex=3)
        
        self.assertEqual(sorted_rects.all(), exp_rects_list.all())
        self.assertEqual(sorted_levels.all(), exp_level_list.all())

    # ----------------------------------------------------------------------------
    
    """
    def test_calculate_histograms (self):

        gray_frame = np.full((60, 60, 1), 2, dtype=np.uint8)
        hsv_frame = np.full((60,60,3), 4, dtype=np.uint8)
        rect_list = [(0,0,20,20), (20,20,20,20)]

        roi = ROITracking(maxTracks=2, historyCount=1)
        incoming_hists = roi.calculateIncomingHistograms(gray_frame, rect_list)
        incoming_hsv_hists = roi.calculateIncomingHSVHistograms(hsv_frame, rect_list)
        self.assertEqual(len(incoming_hists), 2)

        corr_index = roi.getCorrelationList([incoming_hists[0]], [incoming_hsv_hists[0]], [incoming_hists[1]])
        self.assertEqual(corr_index, 0)

    # ------------------------------------------------------------------------------
    
    def test_process (self):

        frame = np.full((60, 60, 1), 2, dtype=np.uint8)
        hsv_frame = np.full((60, 60, 3), 2, dtype=np.uint8)
        rect_list = [(0,0,20,20), (20,20,20,20)]

        roi = ROITracking(maxTracks=3, historyCount=2)
        roi.process(processFrame=frame, hsvFrame=hsv_frame, rects=rect_list, levels=[4.0, 2.0])

        self.assertFalse(roi.tracks[0].isEmpty())
        self.assertFalse(roi.tracks[1].isEmpty())
        self.assertTrue(roi.tracks[2].isEmpty())

"""

        
