
import array, numpy as np, unittest
from app.dependencies.roitracking import TrackData, Track, ROITracking


class TrackTest (unittest.TestCase):

    def test_constructor (self):

        track = Track(historyCount=15)
        self.assertEqual(track.gray_hist_history.shape, (15,256,1))
        self.assertEqual(track.level_history.shape, (15,))

    # -----------------------------------------------------------------
    
    def test_add_tracks (self):

        hist_1 = np.full((256, 1), 4.0, dtype=np.float32)
        hist_2 = np.full((256, 1), 8.0, dtype=np.float32)

        # Create track record and test that it's empty
        track = Track(historyCount=2) 
        self.assertTrue(track.isEmpty()) 

        # Add a non empty hist and level and test
        track.addTrack(TrackData(grayHist=hist_1, level=3.45))
        self.assertEqual(track.gray_hist_history[0].all(), hist_1.all())
        self.assertEqual(track.level_history[0], np.float32(3.45))
        self.assertEqual(track.getLatestHistogram()[0], 0)

        # Now add an empty record and test that the first record is empty
        track.addTrack(TrackData(grayHist=None, level=0.0))
        self.assertEqual(track.gray_hist_history[0].all(), track.generateEmptyHistogram().all())
        self.assertEqual(track.level_history[0], np.float32(0.0))
        self.assertEqual(track.getLatestHistogram()[0], 1)

        # Add a nonempty record
        track.addTrack (TrackData(grayHist=hist_2, level=8.0))

        # Now the first record should be 8.0's and the second record shoud be empty
        self.assertEqual(track.gray_hist_history[0].all(), hist_2.all())
        self.assertEqual(track.level_history[0], np.float32(8.0))
        self.assertEqual(track.getLatestHistogram()[0], 0)

        # The second record shoud be empty
        self.assertEqual(track.gray_hist_history[1].all(), track.generateEmptyHistogram().all())
        self.assertEqual(track.level_history[1], np.float32(0.0))


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
        roi.addTrack(TrackData(grayHist=hist_data, level=level), index=0)

        # Test to see if the latest list is the one you just added
        latest_list = roi.getLatestHistograms()
        
        self.assertEqual(latest_list[0].all(), hist_data.all())

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
    
    def test_calculate_histograms (self):

        frame = np.full((60, 60, 1), 2, dtype=np.uint8)
        rect_list = [(0,0,20,20), (20,20,20,20)]

        roi = ROITracking(maxTracks=2, historyCount=1)
        incoming_hists = roi.calculateIncomingHistograms(frame, rect_list)
        self.assertEqual(len(incoming_hists), 2)

        corr_index = roi.getCorrelationList([incoming_hists[0]], [incoming_hists[1]])
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



        
