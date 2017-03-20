#include "thread.h"
#include "led-matrix.h"
#include "LedServer.h"

#include <assert.h>
#include <unistd.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <algorithm>

using std::min;
using std::max;

// Base-class for a Thread that does something with a matrix.
class RGBMatrixManipulator : public Thread {
public:
  RGBMatrixManipulator(RGBMatrix *m) : running_(true), matrix_(m) {}
  virtual ~RGBMatrixManipulator() { running_ = false; }

  // Run() implementation needs to check running_ regularly.

protected:
  volatile bool running_;  // TODO: use mutex, but this is good enough for now.
  RGBMatrix *const matrix_;
};

// Pump pixels to screen. Needs to be high priority real-time because jitter
// here will make the PWM uneven.
class DisplayUpdater : public RGBMatrixManipulator {
public:
  DisplayUpdater(RGBMatrix *m) : RGBMatrixManipulator(m) {}

  void Run() {
    while (running_) {
      matrix_->UpdateScreen();
    }
  }
};

class SimpleSquare : public RGBMatrixManipulator {
public:
  SimpleSquare(RGBMatrix *m) : RGBMatrixManipulator(m) {}
  void Run() {
    // Diagonaly
    matrix_->SetPixel(1, 1, 0, 0, 255);
  }
};

// -- The following are demo image generators.
int main(int argc, char *argv[]) {
    std::cout << "Starting the LED controller" << '\n';
    // Init server
    GPIO io;
    if (!io.Init())
        return 1;

    RGBMatrix m(&io);
    // SimpleSquare *image_gen = new SimpleSquare(&m);
    RGBMatrixManipulator *updater = new DisplayUpdater(&m);
    LedServer *serv = new LedServer(50007, &m);
    updater->Start(10);  // high priority
    serv->Start(5);
    m.SetPixel(1,1,0,15,0);
    m.SetPixel(2,2,0,16,0);
    // Things are set up. Just wait for <RETURN> to be pressed.
    printf("Press <RETURN> to exit and reset LEDs\n");
    getchar();
    std::cout << "Stopping server.." << '\n';
    // Stopping threads and wait for them to join.
    delete updater;

    // Final thing before exit: clear screen and update once, so that
    // we don't have random pixels burn
    m.ClearScreen();
    m.UpdateScreen();

    return 0;
    }
