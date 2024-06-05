import argparse

from ouca.grading import ans
from ouca.grading import config
from ouca.grading import markers


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


def build_flags(client, args):
    questions = []
    for exercise in client.get_exercises(args.assignment['id']):
        for question in client.get_questions(exercise['id']):
            questions.append(question)

    for result in client.get_results(args.assignment['id'], 'submitted'):
        submissions = {}
        for submission in result['submissions']:
            for i, question in enumerate(questions):
                if question['id'] == submission['question_id']:
                    submissions[i+1] = submission

        if not student_matches(result['users'][0], args.student):
            continue

        print(student_name(result['users'][0]))
        for marker in args.module.markers:
            submission = submissions[marker["question"]]
            if not submission['response']:
                continue

            print(f'- {marker["name"]}:')
            for checker_cls in marker['checkers']:
                try:
                    checker = checker_cls(submissions)
                except markers.SubmissionMissingException:
                    continue

                for flag in checker.check():
                    if args.flag:
                        client.post_comment(
                            f'{config.DISCLAIMER}\n\n{flag}',
                            submission['id'],
                            'Submission'
                        )
                    print(f'  + {flag}')

        print()


def clear_flags(client, args):
    # The ANS API does not seem to give a way to resolve a submission to its
    # parent result (and thus to the student who submitted it); we have to
    # build a mapping from submissions to students ahead of time.
    submission_to_student = {}
    for result in client.get_results(args.assignment['id'], 'submitted'):
        for submission in result['submissions']:
            submission_to_student[submission['id']] = result['users'][0]

    for comment in client.get_comments():
        if comment['commentable_type'] != 'Submission':
            continue

        submission = client.get_submission(comment['commentable_id'])
        if submission['id'] not in submission_to_student:
            # comment is not on a submission belonging to the assignment
            continue

        student = submission_to_student[comment['commentable_id']]
        if not student_matches(student, args.student):
            continue

        client.delete_comment(comment['id'])


def main():
    parser = argparse.ArgumentParser(
        description='Automatically flags submissions in Ans',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        'module',
        help='Module name'
    )
    parser.add_argument(
        '-c', '--course',
        default='Computerarchitectuur',
        help='Course name in ANS',
    )
    parser.add_argument(
        '-a', '--assignment',
        help='Assignment name in ANS; inferred from module if None',
    )
    parser.add_argument(
        '-u', '--school',
        default=config.ANS_SCHOOL_ID,
        help='School ID in ANS',
    )
    parser.add_argument(
        '-s', '--student', action='append',
        help='Filter these students (by email or name)',
    )

    subparsers = parser.add_subparsers(required=True)

    parser_build = subparsers.add_parser('build', help='build flags')
    parser_build.set_defaults(func=build_flags)
    parser_build.add_argument(
        '-f', '--flag',
        action='store_true',
        help='Actually flag submissions in ANS',
    )

    parser_clear = subparsers.add_parser('clear', help='clear flags')
    parser_clear.set_defaults(func=clear_flags)

    client = ans.AnsClient(config.ANS_API_TOKEN)
    args = parser.parse_args()

    if args.module in markers.modules:
        args.module = markers.modules[args.module]
    else:
        raise Exception(f'No markers for {args.module}')

    if not args.assignment:
        args.assignment = args.module.assignment_default

    try:
        args.course, = client.get_courses(args.school, args.course)
    except ValueError:
        raise Exception(f'Did not find course "{args.course}"')

    try:
        args.assignment, = client.get_assignments(
            args.course['id'],
            args.assignment,
        )
    except ValueError:
        raise Exception(f'Did not find assignment "{args.assignment}"')

    args.func(client, args)


if __name__ == '__main__':
    main()
