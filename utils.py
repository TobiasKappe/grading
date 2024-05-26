def split_lines(text):
    return [line.strip() for line in text.split('\n') if line.strip()]


def filter_epigraph(lines):
    filtered_lines = []

    for line in lines:
        if "commentaar onder" in line.lower():
            break

        filtered_lines.append(line)

    return filtered_lines
