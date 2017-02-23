# SmartLight

## Installation requirements (Linux)

The following packages are only needed to install PyAudio. After PyAudio is
installed, they can be removed. PyAudio is needed to use the microphone for
speech recognition.

    sudo apt-get install portaudio19-dev python3-all-dev

## Requirements
 - Opencv2 for face detection ([Windows](http://bfy.tw/9v3O), [Linux](https://github.com/jayrambhia/Install-OpenCV))
 - Python 3 (non anaconda)
 - packages in requirements.txt (run `pip3 install -r requirements.txt`)
 - [OpenFace](https://github.com/cmusatyalab/openface). There are a lot of other requirements that need to be satisfied before installing OpenFace, so be aware of that

## Testing
To test the installation of the speech recognition, run:

    python3 -m speech_recognition
