def encode(xpos, ypos, width, height, red=True, green=True, blue=True,
           color_bits=4):
    """
    Given the position and color of the leds, encodes this information in an
    int of 3 bytes, which can be decoded using decode

    0 <= xpos <= 31: 5 bits
    0 <= ypos <= 16: 4 bits
    """

    # input validation first
    if not 0 <= xpos <= 31:
        raise ValueError('The x-position has to be between 0 and 31 inclusive'
                         'to fit the size of the board')
    elif not 0 <= ypos <= 15:
        raise ValueError('The y-position has to be between 0 and 15 inclusive'
                         'to fit the size of the board')
    elif width < 1:
        raise ValueError('The width value has to be higher than 0')
    elif height < 1:
        raise ValueError('The height value has to be higher than 0')
    elif width + xpos > 32:
        raise ValueError('The width and the x-position combined should not'
                         'go over the edge of the board')
    elif height + ypos > 16:
        raise ValueError('The height and the y-position combined should not'
                         'go over the edge of the board')

    signal = 0
    signal += xpos
    signal <<= 4    # size of ypos
    signal += ypos
    signal <<= 5    # size of width
    signal += width
    signal <<= 4    # size of height
    signal += height

    signal <<= color_bits    # size of colour bits
    signal += encode_color(red, color_bits)
    signal <<= color_bits    # size of colour bits
    signal += encode_color(green, color_bits)
    signal <<= color_bits    # size of colour bits
    signal += encode_color(blue, color_bits)

    return signal


def encode_color(color, n_bits):
    """
    If color is given as boolean, interpret it as maximally on or totally off.
    Otherwise check whether it fits within the number of bits.
    """
    if isinstance(color, bool):
        return (2 ** n_bits - 1) * color
    elif 0 <= color < 2 ** n_bits:
        return color
    else:
        raise ValueError(
            "`color` should be a boolean or be between 0 and 2 ** n_bits - 1"
        )


def decode(signal, color_bits=4):
    # colour
    blue = signal & (2 ** color_bits - 1)
    signal >>= color_bits
    green = signal & (2 ** color_bits - 1)
    signal >>= color_bits
    red = signal & (2 ** color_bits - 1)
    signal >>= color_bits

    # height and width
    height = signal & 2**4-1
    signal >>= 4
    width = signal & 2**5-1
    signal >>= 5

    # position
    ypos = signal & 2**4-1
    signal >>= 4
    xpos = signal & 2**5-1

    return xpos, ypos, width, height, red, green, blue


if __name__ == '__main__':
    a = encode(4, 5, 5, 8, blue=1)
    print(a)
    print('{:b}.'.format(a))
    print(decode(a))
