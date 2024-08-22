class SubmissionMissingException(BaseException):
    pass


class Checker:
    show_values = 10

    def __init__(self, students, question, submissions, files, **kwargs):
        self.students = students
        self.question = question
        self.submissions = submissions
        self.files = files

    def check(self):
        raise NotImplementedError

    def analyze_errors(self, errors):
        lines = []
        lines.append('<table>')
        lines.append('<tr><th>Input</th><th>Expected</th><th>Output</th></tr>')
        for value, expected, outcome in errors[:self.show_values]:
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
            f'here is a table of the first {self.show_values}:\n' +
            '\n'.join(lines)
        )

    @staticmethod
    def parametrize(*parameters):
        def decorator(cls):
            def wrapper(**arguments):
                class WrappedChecker(cls):
                    def __init__(self, *args, **kwargs):
                        for param in parameters:
                            setattr(self, param, arguments[param])
                        super().__init__(*args, **kwargs)
                return WrappedChecker
            return wrapper
        return decorator
