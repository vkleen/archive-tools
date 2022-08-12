import hashlib

ARCHIVE_ID_PERSON = hashlib.blake2b(b'paperless.kleen.org/v1 archive id generator', digest_size=16).digest()
BOX_ID_PERSON = hashlib.blake2b(b'paperless.kleen.org/v1 box id generator', digest_size=16).digest()

def new_archive_id(data, key=b''):
    return int.from_bytes(hashlib.blake2b(data, key=key, person=ARCHIVE_ID_PERSON, digest_size=4).digest(), byteorder='little') & 0x7fffffff

def box_id_bytes(data, key=b''):
    return hashlib.blake2b(data, key=key, person=BOX_ID_PERSON, digest_size=16).digest()
