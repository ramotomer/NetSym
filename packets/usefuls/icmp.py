def get_icmp_data(length: int) -> str:
    """
    Get the default data for the ping (abcdefghi...) with a given length
    """
    return ''.join(chr(range(ord('a'), ord('z') + 1)[i % 26]) for i in range(length))
