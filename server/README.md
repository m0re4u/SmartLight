# SmartLight server
-----

This controller uses code from [here](https://github.com/Boomerific/rpi-rgb-led-matrix) and the sample code from [here](http://www.linuxhowtos.org/C_C++/socket.htm). We followed [this tutorial](https://learn.adafruit.com/connecting-a-16x32-rgb-led-matrix-panel-to-a-raspberry-pi) to connect the Pi. Only one row of LEDS can be on simultaneously. More detailed explanation about the LED matrix [here](http://www.rayslogic.com/propeller/programming/AdafruitRGB/AdafruitRGB.htm)


## Pin meanings

Pins can only have a `high` or `low` value. On a 16x32 board two rows are
controlled simultaneously (row `n` and row `n + 1`).

Board pin  | description        | Pi pin           | baby languages
---------- | ------------------ | ---------------- | --------------
R1         | Red 1st bank       | GPIO 17          | red LED on top row
G1         | Green 1st bank     | GPIO 18          | green LED on top row
B1         | Blue 1st bank      | GPIO 22          | blue LED on top row
R2         | Red 2nd bank       | GPIO 23          | red LED on bottom row
G2         | Green 2nd bank     | GPIO 24          | green LED on bottom row
B2         | Blue 2nd bank      | GPIO 25          | blue LED on bottom row
A, B, C    | Row address        | GPIO 7, 8, 9     | a 3-bit address of the row that is on
OE-        | neg. Output enable | GPIO 2           | whether the boards is on at all
CLK        | Serial clock       | GPIO 3           | shift all the RGB values once and give the first LED the selected colours
STR        | Strobe row data    | GPIO 4           | make LEDs show current row data

## Protocol
rectangle (xpos, ypos, xsize, ysize)
on/off
