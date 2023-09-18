
import numpy as np, unittest
from app.dependencies.roitracking import Track, ROITracking


class TrackTest (unittest.TestCase):

    def test_constructor (self):

        track = Track(historyCount=15)
        self.assertEqual(track.corr_hist_history.shape, (15,256,1))
        self.assertEqual(track.levels_history.shape, (15,))

    
    # -----------------------------------------------------------------
    
    def test_add_tracks (self):

        hist_1 = np.full((256, 1), 4.0, dtype=np.float32)
        hist_2 = np.full((256, 1), 8.0, dtype=np.float32)

        # Create track record and test that it's empty
        track = Track(historyCount=2) 
        self.assertTrue(track.isEmpty()) 

        # Add a non empty hist and level and test
        track.addTrack(hist=hist_1, level=3.45)
        self.assertEqual(track.corr_hist_history[0].all(), hist_1.all())
        self.assertEqual(track.levels_history[0], np.float32(3.45))
        self.assertEqual(track.getLatestHistogram()[0], 0)

        # Now add an empty record and test that the first record is empty
        track.addTrack(hist=None, level=0.0)
        self.assertEqual(track.corr_hist_history[0].all(), track.generateEmptyHistogram().all())
        self.assertEqual(track.levels_history[0], np.float32(0.0))
        self.assertEqual(track.getLatestHistogram()[0], 1)

        # Add a nonempty record
        track.addTrack (hist=hist_2, level=8.0)

        # Now the first record should be 8.0's and the second record shoud be empty
        self.assertEqual(track.corr_hist_history[0].all(), hist_2.all())
        self.assertEqual(track.levels_history[0], np.float32(8.0))
        self.assertEqual(track.getLatestHistogram()[0], 0)

        # The second record shoud be empty
        self.assertEqual(track.corr_hist_history[1].all(), track.generateEmptyHistogram().all())
        self.assertEqual(track.levels_history[1], np.float32(0.0))


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
        roi.addTrack(hist=hist_data, level=level, index=0)

        # Test to see if the latest list is the one you just added
        latest_list = roi.getLatestHistograms()
        
        self.assertEqual(latest_list[0].all(), hist_data.all())