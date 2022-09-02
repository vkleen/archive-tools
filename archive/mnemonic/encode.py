from .wordlist import wordlist
import itertools

BASE = len(wordlist)
assert BASE*BASE*BASE >= 2**32

def encode32(x: int):
    if x >= 2**32 or x < 0:
        raise ValueError("encode32 only takes 4 bytes at a time")
    return (x // BASE // BASE, (x // BASE) % BASE, x % BASE)

def to_words(tuple):
    return (wordlist[x] for x in tuple)

def chunked_bytes(gen, max_size):
    it = iter(gen)
    for first in it:
        yield bytes(itertools.chain([first], itertools.islice(it, max_size-1)))

def encode(src: bytes, sep = '--', word_sep = '-') -> str:
    chunks = (word_sep.join(to_words(encode32(int.from_bytes(bs, byteorder='big')))) for bs in chunked_bytes(src, 4))
    return sep.join(chunks)

def encoded(src: bytes):
    return itertools.chain.from_iterable(to_words(encode32(int.from_bytes(bs, byteorder='big'))) for bs in chunked_bytes(src, 4))
