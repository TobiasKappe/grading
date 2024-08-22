# Partially automated grading in [Ans](https://ans.app/)

This library can help you automate some tasks when grading assignments in [Ans](https://ans.app/).
Basically, it gives you a way to run scripts on each answer, while adding the output of those scripts as flags.

## API stability

_Caveat emptor_: this library has grown organically to fit the needs of its author; as a result, the code can be unpolished in places.
The API may also change over time; you may want to pin your copy of this code to a specific version to keep it working.

## Importing the code

Currently, the best way to use the code in your project is to use a git submodule:

```console
$ git submodule add git@github.com:TobiasKappe/grading.git
```

If you are using [`poetry`](https://python-poetry.org/), you can easily make the library available by adding the following to `pyproject.toml` (if the `tool.poetry.dependencies` section already exists, add the second line there).

```ini
[tool.poetry.dependencies]
grading = { path = "./grading", develop = true }
```

After that, run `poetry lock` and `poetry install`, and you should be able to import the `grading` module in your environment now (don't forget to activate your `poetry shell` too).

## Architecture

The library is built around three concepts:
* A _checker_ is a class that can be instantiated to verify the answer to a question.
  It may return an iterable of strings, each of which should be added as a flag to the answer in Ans.
* A _marker_ is a Python module that connects checkers to questions within an assignment.
  Each checker can also be configured with question-specific parameters.
* A _flagger_ is a script that calls the built-in flagging script, along with a bunch of arguments.
  Additionally, a flagger holds a list of marker modules to be exposed to the user.

There are probably better ways to do this, and I am not too keen on the names, but it works.

## Tutorial

Let's work through a toy example; with a little bit of puzzling, you should be able to customize this to your needs.

Suppose you had an assignment where students are asked to perform some hard calculation.
Furthermore, because you are a charitable teacher, you also decide to build in a 10% tolerance.

### Checker

First, let's build a checker and save it to `calculation.py`:

```python
from grading.checker import Checker

@Checker.parametrize('right_answer', 'tolerance')
class CalculationChecker(Checker):
    def __init__(self, students, question, submissions, files, **kwargs):
        self.answer = submissions[question]['response']

    def check(self):
        try:
            answer_numeric = float(self.answer)
        except ValueError:
            yield 'Answer cannot be parsed as a float.'
            return

        if answer_numeric == self.right_answer:
            yield 'Answer is exactly right!'
        elif answer_numeric < (1 - self.tolerance) * self.right_answer:
            yield (
                f'Answer below {self.tolerance} '
                f'tolerance of {self.right_answer}.'
            )
        elif answer_numeric > (1 + self.tolerance) * self.right_answer:
            yield (
                f'Answer above {self.tolerance} '
                f'tolerance of {self.right_answer}.'
            )
        else:
            yield (
                f'Answer within {self.tolerance} '
                f'tolerance of {self.right_answer}.'
            )
```

The constructor has several parameters:
* `students` is a list of [raw user objects](https://ans.app/api/docs/index.html#/Users/get_api_v2_users__id_) obtained from Ans, holding information about the students who made the submission (possibly more than one, in the case of group assignments).
* `question` is the question number that this checker is being run against; it can be used to index into `submissions`.
* `submissions` corresponds to the assignment that the checker is being run against; it maps question numbers to a [raw submission object](https://ans.app/api/docs/index.html#/Submissions/get_api_v2_submissions__id_) from Ans.
* `files` contains information about files that were submitted as attachments by the student; concretely, each element is a pair consisting of a file name (as chosen by the student!) and its contents.

### Marker

Next, we need to build a marker to configure our checker, and point it to the right question.
To this end, we create `mark_calculation.py` and put in the following:

```python
from calculation import CalculationChecker

markers = [{
    "question": 7,
    "name": "The Big Calculation Question",
    "checkers": [
        CalculationChecker(
            right_answer=42,
            tolerance=0.1
        ),
    ]
}]

assignment_default = 'The Assignment with the Big Calculation'
```

Concretely, a marker module is expected to have at least two values in it:
* `markers` is a list of dictionaries, each of which holds information about checkers.
  In this case, there is one dictionary that points to question 7, which holds one instance of `CalculationChecker` instantiated with a right answer and the 10% tolerance mentioned before.
  The `name` attribute is required, but purely cosmetic; it will only show up in the output of the flagger script.
* `assignment_default` is the default name of the assignment (in Ans) that this marker should run against.
  It can be overridden by at run-time.

### Flagger

The last piece of the puzzle is to configure the flagger script.
This can be by putting the following in a file, say `flagger.py`:

```python
from grading.flagger import main

import mark_calculation

modules = {
    'calc': mark_calculation,
}

main(
    'The Course with the Big Calculation',
    modules,
    ans_school_id,
    'ans_api_token',
)
```

The first argument to `main` is the default name of the course (in Ans) to grade; it can be overridden at run-time.
The second argument is a dictionary mapping short assignment names to modules that mark them.
The third and fourth arguments are a [school ID and API token](https://ans.app/users/tokens) that you must obtain from Ans.

### Running

Finally, we can run our flagging script

```console
$ python flagger.py calc build
```

This will do a dry-run on all of the submissions to _"The Assignment with the Big Calculation"_ in _"The Course with the Big Calculation"_ and print the flags that would be added.
To actually add the flags, you can run

```console
$ python flagger.py calc build -f
```

You can clear all flags by running

```console
$ python flagger.py calc clear
```

Finally, one useful feature is to run the script only on submissions that currently do not have any flags:

```console
$ python flagger.py calc build -u
```

Again, you should add `-f` if you want the flags to actually be placed.

Further options are available; run `python flagger.py --help` for an overview.
