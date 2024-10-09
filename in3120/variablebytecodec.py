# pylint: disable=missing-module-docstring
# pylint: disable=consider-using-f-string

from struct import pack
from typing import Tuple
from bitarray import bitarray


class VariableByteCodec:
    """
    A simple encoder/decoder for variable-byte codes. See Figure 5.8 in
    https://nlp.stanford.edu/IR-book/pdf/05comp.pdf for details.

    This algo. work best for number that is under the threshold of 2**(7*n).
    Inverted index has some big nunber, but not many.
    """

    @staticmethod
    def encode(number: int, destination: bitarray) -> int:
        """
        Encodes the given number, and appends the resulting bytes to the given
        destination buffer. Returns the number of bits that were appended.
        """
        assert destination is not None
        assert number >= 0

        if number == 0:
            destination.extend([1] + [0]*7)
            return 8
        
        
        # Add bit to segment and shift to the right (next number)
        segments = []
        while number > 0:
            segments.append(number % 128)
            number //= 128
        segments[0] += 128

        for seg in reversed(segments):
            for bit in range(7, -1, -1):
                destination.append((seg >> bit) & 1)
        
        return len(segments) * 8

    @staticmethod
    def decode(source: bitarray, start: int) -> Tuple[int, int]:
        """
        Starting at the given position in the source buffer, decodes the next number.
        Returns a pair comprised of the decoded number, and the number of bytes
        read from the source buffer.
        """
        assert source is not None
        assert start >= 0

        number = 0
        n_segments = 0

        while True:
            n_segments += 1 
             
            # Shift old number over one bit, and consume next bit. 
            for bit in range(1,8):
                number = (number << 1) | source[start+bit]

            if source[start] == 1:  # if first bit is 1, done. If 0 read next byte.
                return (number, n_segments*8)
            else:
                start += 8


class GammaCodec:
    """
    Work best on numbers that are close to 1. Since must of the numbet in the inverted index are 1.
    This algo. is good for that.

    """

    @staticmethod
    def encode(number: int, destination: bitarray) -> int:

        assert number > 0

        # Extraxt lengt, and get as many 0 as n.
        n = number.bit_length()
        destination.extend([0] *n)

        # copy the number to dest. By shifting 
        for i in range(n -1,-1,-1 ):
            destination.append((number >> i) & 1)

        return (2*n)
       
    @staticmethod
    def decode(source: bitarray, start: int) -> Tuple[int, int]:
        n: int = 0
        while source[start + n] == 0:
            n += 1

        # jump over all zeros
        binary_version = source[start + n:start + 2* n] 
        
        number = 0
        for bit in binary_version:
            number = (number << 1) | bit

        # Return the decoded number and the number of bits consumed
        return (number, 2 * n)