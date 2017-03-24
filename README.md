# SmartLight

## Installation requirements (Linux)

The following package is only needed to install PyAudio. After PyAudio is
installed, they can be removed. PyAudio is needed to use the microphone for
speech recognition.

    sudo apt-get install portaudio19-dev python3-all-dev

These packages are needed to install OpenFace.

    sudo apt-get install portaudio19-dev python3-all-dev
    sudo apt-get install cmake

## Requirements
 - Python 3.5 or higher (non anaconda (for Opencv2))
 - packages in requirements.txt (run `pip3 install -r requirements.txt`)
 - [OpenFace](https://github.com/cmusatyalab/openface). There are a lot of other requirements that need to be satisfied before installing OpenFace, so be aware of that. See the [installation guide](https://cmusatyalab.github.io/openface/setup/).
    - Install Opencv2 ([Windows](http://bfy.tw/9v3O), [Linux](https://github.com/jayrambhia/Install-OpenCV))
    - Run (~5 minutes): `pip install dlib`
    - Install [Torch](http://torch.ch/docs/getting-started.html) (~ 20 minutes)
    - Run (~10 seconds): `pip install git+https://github.com/cmusatyalab/openface`


## Testing
To test the installation of the speech recognition, run:

    python -m speech_recognition
