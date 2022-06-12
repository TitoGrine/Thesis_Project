def get_fuzziness_distance(string_length: int) -> int:
    if string_length > 5:
        return 2
    if string_length > 2:
        return 1

    return 0
