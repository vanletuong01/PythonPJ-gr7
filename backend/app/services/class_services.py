def generate_short_class_name(year: str, major_code: str, class_code: str):
    return f"{year[-2:]}{major_code}{class_code[-2:]}"