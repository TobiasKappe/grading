def split_lines(text):
    return [line.strip() for line in text.split('\n') if line.strip()]


def filter_epigraph(lines):
    filtered_lines = []

    for line in lines:
        if "commentaar onder" in line.lower():
            break

        filtered_lines.append(line)

    return filtered_lines


def student_name(user):
    if user['middle_name']:
        return (
            f'{user["first_name"]} '
            f'{user["middle_name"]} '
            f'{user["last_name"]}'
        )
    else:
        return (
            f'{user["first_name"]} '
            f'{user["last_name"]}'
        )


def student_matches(user, students):
    if not students:
        return True

    if user['email'] in students:
        return True

    if student_name(user) in students:
        return True

    return False
