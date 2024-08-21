class SubmissionMissingException(BaseException):
    pass


class Checker:
    def __init__(self):
        raise NotImplementedError

    def check(self):
        raise NotImplementedError

    def analyze_errors(self, errors):
        lines = []
        lines.append('<table>')
        lines.append('<tr><th>Input</th><th>Expected</th><th>Output</th></tr>')
        for value, expected, outcome in errors[:self.SHOW_VALUES]:
            lines.append(
                f'<tr>'
                f'<td>{value}</td>'
                f'<td>{expected}</td>'
                f'<td>{outcome}</td>'
                f'</tr>'
            )
        lines.append('</table>')

        yield (
            f'Got {len(errors)} unexpected outcomes; ' +
            f'here is a table of the first {self.SHOW_VALUES}:\n' +
            '\n'.join(lines)
        )
