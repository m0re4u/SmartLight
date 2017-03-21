import pyaudio
import numpy as np
import pylab
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
    def __init__(self, recordingDevice=None, startStream=True):
        logger.debug("-- Initalize Prep Detector")

        self.chunk = 1028  # number of data points to read at a time
        self.rate = 11025  # time resolution of recordingdevice (Hz)
        self.threshold = 0.5*(10**9)
        # internal datastructure for stream buffer
        logger.debug("-- Creating Stream Buffer")
        self.soundBufferLength = 4  # length of internal buffer
        self.soundBuffer = np.zeros(self.soundBufferLength*self.rate)

        # setup and start PyAudio stream
        logger.debug("-- Creating Stream Object")
        self.p = pyaudio.PyAudio()  # start the PyAudio class
        if startStream:
            self.stream_start()

        # Threading infrastructure
        self.stop_recognising = Event()
        self.thread = Thread(
            name="Clapdetect",
            target=self.detect_naive_continuously
        )

    # Basic functions for interaction with stream
    def stream_read(self):
        """return values for a single chunk"""
        data = np.fromstring(self.stream.read(self.chunk), dtype=np.int32)
        return data

    def stream_start(self):
        """connect to the audio device and start a stream"""
        logger.debug("-- stream OPENED")
        self.stream = self.p.open(format=pyaudio.paInt32, channels=1,
                                  rate=self.rate, input=True,
                                  frames_per_buffer=self.chunk)

    def stream_stop(self):
        """close the stream but keep the PyAudio instance alive."""
        if 'stream' in locals():
            self.stream.stop_stream()
            self.stream.close()
        logger.debug("-- stream CLOSED")

    def close(self):
        """gently detach from things."""
        self.stream_stop()
        self.p.terminate()
        logger.debug("-- process TERMINATED")

    # Buffer Functions
    def buffer_add(self):
        """add a single chunk to the buffer."""
        self.soundBuffer[:-self.chunk] = self.soundBuffer[self.chunk:]
        self.soundBuffer[-self.chunk:] = self.stream_read()

    def buffer_flush(self):
        """completely flush buffer (purge all data that is in there)."""

    # Lights On function
    def light_on(config_file, methode="naive"):
        # TODO IMPLEMENT CHOICE FOR DETECTOR
        listener = AudioListener()
        if methode == "naive":
            switch = listener.find_clap_naive()
        else:
            listener.find_clap_deriv()
        listener.close()
        if switch:
            return {True, True, True}
        else:
            return

    def buffer_plot(self, saveAs="03.png"):
        """plot what's in the tape."""
        pylab.plot(np.arange(len(self.soundBuffer))/self.rate,
                   self.soundBuffer)
        pylab.axhline(y=self.threshold, color='r')
        pylab.axis([0, self.soundBufferLength, -2**31, 2**31])
        if saveAs:
            pylab.savefig(saveAs, dpi=50)
        pylab.close('all')
        logger.debug("-- Plot Saved")

    # Clap find functions
    def find_clap_naive(self):
        """Naive way of finding clap above a threshold."""
        # Initiate variables
        claps = 0
        iterations = 0
        # Load data into buffer from stream
        while(claps < 2):
            # Fill buffer slot
            for i in range(0, self.soundBufferLength):
                self.buffer_add()
            # Log
            logger.debug("-- done with buffer loading")
            logger.debug("-- checking for peaks")
            # Find peaks
            # Reset clap count after 5 iterations (preventing false pos)
            iterations += 1
            if iterations > 5 and claps == 1:
                claps = 0
                logger.debug("-- Clap count reset")
            if np.amax(self.soundBuffer) > self.threshold:
                logger.info("-- Found Clap")
                claps += 1
                iterations = 0
                with open('datadump{}.txt'.format(claps), 'w') as f:
                    f.write(str(self.soundBuffer.tolist()))
                self.buffer_plot("{}.png".format(claps))
                self.soundBuffer = np.zeros(self.soundBufferLength*self.rate)
                logger.debug("-- Flushing Buffer")
        logger.debug("-- Found {} Claps".format(claps))
        if claps == 2:
            return True
        else:
            return False

    def diff_list(olist):
        difflist = [0]
        for i in range(0, len(olist)-1):
            difflist.append(olist[i+1]-olist[i])
        return difflist

    def find_clap_deriv(self, saveAs="deriv.png"):
        claps = 0
        iterations = 0
        while(claps < 2):
            for i in range(0, self.soundBufferLength):
                self.buffer_add()
            logger.debug("-- done with buffer loading")
            logger.debug("-- checking for peaks")
            deriv = self.diff_list(self.soundBuffer)
            iterations += 1
            if iterations > 5 and claps == 1:
                claps = 0
                logger.debug("-- Clap count reset")
            if np.amax(deriv) > self.threshold:
                logger.info("-- Found Clap")
            pylab.plot(np.arange(len(deriv))/self.rate,
                       deriv)
            pylab.axis([0, self.soundBufferLength, -2**31, 2**31])
            if saveAs:
                pylab.savefig(saveAs, dpi=50)
            pylab.close('all')
        return True

    def find_clap_stat(self):
        for i in range(0, self.soundBufferLength):
            self.buffer_add()
            logger.debug(i)
        self.soundBuffer = abs(self.soundBuffer)


if __name__ == "__main__":
    logging.basicConfig(level="INFO")
    listener = AudioListener()
    listener.find_clap_naive()
    listener.close()
    logger.debug("TEST COMPLETE")
