CFLAGS=-Wall -O3 -g
CXXFLAGS=-Wall -O3 -g -std=c++11 -Wextra -pedantic
S_OBJECTS=main.o gpio.o led-matrix.o thread.o LedServer.o
S_BINARIES=server
LDFLAGS=-lrt -lm -lpthread

all : $(S_BINARIES)

led-matrix.o: led-matrix.cpp led-matrix.h
main.o: led-matrix.h
LedServer.o: LedServer.cpp LedServer.h

server: $(S_OBJECTS)
	$(CXX) $(CXXFLAGS) $^ -o $@ $(LDFLAGS)

clean:
	rm -f $(S_OBJECTS) $(S_BINARIES)
