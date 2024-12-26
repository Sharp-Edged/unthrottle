import string

def file_size_to_bytes(file_size: str) -> int:
    units = { "B": 1, "KB": 10**3, "MB": 10**6, "KiB": 2**10, "MiB": 2**20}
    size = file_size.rstrip(string.ascii_letters)
    unit = file_size[len(size):]
    return int(float(size) * units[unit])
