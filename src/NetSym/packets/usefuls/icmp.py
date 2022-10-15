def get_icmp_data(length: int) -> bytes:
    """
    Get the default data for the ping (abcdefghi...) with a given length
    """
    return b''.join(chr(range(ord('a'), ord('z') + 1)[i % 26]).encode('ascii') for i in range(length))
