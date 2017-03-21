import pyaudio
import numpy as np
import logging
from threading import Thread, Event

logger = logging.getLogger(__name__)


class AudioListener(object):
    """
    Continuously listen to audio stream
    To do this load a portion of the stream into a temporary
    memory and do computations on that.
    """
    # Framework for class from
    # http://www.swharden.com/wp/2016-07-19-realtime-audio-visualization-in-python/
    def __init__(self, chunk_size=1028, buffer_length=4, max_distance=5,
                 sample_rate=11025, threshold=0.5e9, method='naive', nclaps=2):
        logger.debug("Initialise Prep Detector")

        # number of data points to read at a time
        self.chunk = chunk_size
        # time resolution of recordingdevice (Hz)
        self.rate = sample_rate
        self.soundBufferLength = buffer_length
        self.threshold = threshold

        # internal data structure for stream buffer
        logger.debug("Creating Stream Buffer")
        # length of internal buffer
        self.soundBuffer = np.zeros(self.soundBufferLength*self.rate)

        # set up and start PyAudio stream
        logger.debug("Creating Stream Object")
        self.p = pyaudio.PyAudio()  # start the PyAudio class

        # Threading infrastructure
        self.light_state = False

        self.stop_recognising = Event()
        self.thread = Thread(
            name="Clapdetect",
            target=self.detect_continuously,
            kwargs=dict(
                method=method,
                nclaps=nclaps,
                max_distance=max_distance
            )
        )

    # Basic functions for interaction with stream
    def stream_read(self):
        """return values for a single chunk"""
        data = np.fromstring(self.stream.read(self.chunk), dtype=np.int32)
        return data

    def stream_start(self):
        """connect to the audio device and start a stream"""
        logger.debug("stream OPENED")
        self.stream = self.p.open(format=pyaudio.paInt32, channels=1,
                                  rate=self.rate, input=True,
                                  frames_per_buffer=self.chunk)

    def stream_stop(self):
        """close the stream but keep the PyAudio instance alive."""
        if 'stream' in locals():
            self.stream.stop_stream()
            self.stream.close()
        logger.debug("stream CLOSED")

    def start(self):
        self.stream_start()
        self.start_thread()

    def stop(self):
        """gently detach from things."""
        if self.thread.is_alive():
            self.stop_thread()
        self.stream_stop()
        self.p.terminate()
        logger.debug("process TERMINATED")

    def start_thread(self):
        """Start the thread that recognises claps"""
        self.stop_recognising.clear()
        self.thread.start()

    def stop_thread(self):
        """Tell the thread to stop and block until it does."""
        self.stop_recognising.set()
        self.thread.join()

    # Buffer Functions
    def buffer_add(self):
        """add a single chunk to the buffer."""
        self.soundBuffer[:-self.chunk] = self.soundBuffer[self.chunk:]
        self.soundBuffer[-self.chunk:] = self.stream_read()

    def buffer_flush(self):
        """completely flush buffer (purge all data that is in there)."""

    def detect_continuously(self, method, **kwargs):
        while not self.stop_recognising.is_set():
            if method == "naive":
                self.find_clap_naive(**kwargs)
            else:
                self.find_clap_deriv(**kwargs)
            self.light_state = not self.light_state

    # Lights On function
    def light_on(self):
        return (self.light_state,) * 3

    def buffer_plot(self, saveAs="03.png"):
        """plot what's in the tape."""
        import pylab
        pylab.plot(np.arange(len(self.soundBuffer))/self.rate,
                   self.soundBuffer)
        pylab.axhline(y=self.threshold, color='r')
        pylab.axis([0, self.soundBufferLength, -2**31, 2**31])
        if saveAs:
            pylab.savefig(saveAs, dpi=50)
        pylab.close('all')
        logger.debug("Plot Saved")

    # Clap find functions
    def find_clap_naive(self, saveAs=None, nclaps=2, max_distance=5):
        """
        Naive way of finding clap above a threshold.
        Blocks until `nclaps` are found within `max_distance` iterations
        """
        # Initiate variables
        claps = 0
        iterations = 0
        # Load data into buffer from stream
        while not self.stop_recognising.is_set() and claps < nclaps:
            # Fill buffer slot
            for i in range(0, self.soundBufferLength):
                self.buffer_add()
            # Log
            logger.debug("done with buffer loading")
            logger.debug("checking for peaks")
            # Find peaks
            # Reset clap count after 5 iterations (preventing false pos)
            iterations += 1
            if iterations > max_distance and claps > 0:
                claps = 0
                logger.debug("Clap count reset")
            if np.amax(self.soundBuffer) > self.threshold:
                logger.info("Found Clap")
                claps += 1
                iterations = 0
                if saveAs is not None:
                    with open('{}{}.txt'.format(saveAs, claps), 'w') as f:
                        f.write(str(self.soundBuffer.tolist()))
                    self.buffer_plot("{}{}.png".format(saveAs, claps))
                self.soundBuffer = np.zeros(self.soundBufferLength*self.rate)
                logger.debug("Flushing Buffer")
        logger.debug("Found {} Claps".format(claps))

    @staticmethod
    def diff_list(olist):
        difflist = [0]
        for i in range(0, len(olist)-1):
            difflist.append(olist[i+1]-olist[i])
        return difflist

    def find_clap_deriv(self, saveAs=None, nclaps=2, max_distance=5):
        """
        Block until the `nclaps` claps are found, all within `max_distance`
        iterations.
        """
        claps = 0
        iterations = 0
        while not self.stop_recognising.is_set() and claps < nclaps:
            for i in range(0, self.soundBufferLength):
                self.buffer_add()
            logger.debug("done with buffer loading")
            logger.debug("checking for peaks")
            deriv = self.diff_list(self.soundBuffer)
            # The following two if-statements were edited by Martin because
            # he thought this would fix the logic
            if claps > 0:
                iterations += 1
            if iterations > max_distance:
                claps = 0
                iterations = 0
                logger.debug("Clap count reset")
            if np.amax(deriv) > self.threshold:
                logger.info("Found Clap")
                claps += 1
            if saveAs is not None:
                import pylab
                pylab.plot(np.arange(len(deriv))/self.rate,
                           deriv)
                pylab.axis([0, self.soundBufferLength, -2**31, 2**31])
                pylab.savefig(saveAs, dpi=50)
                pylab.close('all')
        # return True

    def find_clap_stat(self):
        for i in range(0, self.soundBufferLength):
            self.buffer_add()
            logger.debug(i)
        self.soundBuffer = abs(self.soundBuffer)


if __name__ == "__main__":
    from time import sleep
    logging.basicConfig(level="INFO")
    listener = AudioListener()
    listener.start()

    for i in range(10):
        print(listener.light_on())
        sleep(1)
    # listener.stream_start()
    # listener.find_clap_deriv()
    listener.stop()
    logger.debug("TEST COMPLETE")
