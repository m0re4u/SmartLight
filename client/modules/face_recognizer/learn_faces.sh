#! /bin/bash
pushd ~/projects/openface/
./util/align-dlib.py ~/projects/uni/mu/client/modules/face_recognizer/raw_data/ align outerEyesAndNose ~/projects/uni/mu/client/modules/face_recognizer/aligned_data/ --size 96
./batch-represent/main.lua -outDir ~/projects/uni/mu/client/modules/face_recognizer/features/ -data ~/projects/uni/mu/client/modules/face_recognizer/aligned_data/
./demos/classifier.py train ~/projects/uni/mu/client/modules/face_recognizer/features/
popd
