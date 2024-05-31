import argparse

import requests

from ouca.grading import ans
from ouca.grading import config
from ouca.grading import markers

from ouca.grading.utils import student_name, student_matches


def build_flags(client, args):
    questions = []
    for exercise in client.get_exercises(args.assignment['id']):
        for question in client.get_questions(exercise['id']):
            questions.append(question)

    for result in client.get_results(args.assignment['id'], 'submitted'):
        files = []
        for file in result['files']:
            response = requests.get(file['url'])
            files.append((file['file_name'], response.text))

        submissions = {}
        for submission in result['submissions']:
            for i, question in enumerate(questions):
                if question['id'] == submission['question_id']:
                    submissions[i+1] = submission

        if args.before and result['submitted_at'] > args.before:
            continue
        if args.after and result['submitted_at'] < args.after:
            continue

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
                    checker = checker_cls(
                        result['users'][0],
                        marker['question'],
                        submissions,
                        files
                    )
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
    # build a mapping from submissions to results ahead of time.
    submission_to_result = {}
    for result in client.get_results(args.assignment['id'], 'submitted'):
        for submission in result['submissions']:
            submission_to_result[submission['id']] = result

    for comment in client.get_comments():
        if comment['commentable_type'] != 'Submission':
            continue

        submission_id = comment['commentable_id']
        if submission_id not in submission_to_result:
            # comment is not on a submission belonging to the assignment
            continue

        result = submission_to_result[submission_id]

        try:
            submission = client.get_submission(submission_id)
        except ans.AnsForbiddenException:
            print(
                f'Could not access submission #{submission_id} '
                f'which belongs to result {result["id"]}.'
            )
            continue

        if not student_matches(result['users'][0], args.student):
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
    parser.add_argument(
        '--before',
        help='Only consider results submitted on or before the given time'
    )
    parser.add_argument(
        '--after',
        help='Only consider results submitted at or after the given time'
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
