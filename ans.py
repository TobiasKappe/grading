from ouca.grading.rest import RestSession


class AnsClient(RestSession):
    BASE_URL = "https://ans.app/api/v2/"
    ITEMS_PER_PAGE = 100

    def __init__(self, api_token):
        self.api_token = api_token
        super().__init__()
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Accept': 'application/json',
        }

    def get_pages(self, path, *args, **kwargs):
        if 'params' not in kwargs:
            kwargs['params'] = {}
        kwargs['params']['items'] = self.ITEMS_PER_PAGE
        kwargs['params']['page'] = 1

        items = []
        while True:
            page = self.get(path, *args, **kwargs)
            items += page.json()
            if page.headers['Current-Page'] == page.headers['Total-Pages']:
                return items
            kwargs['params']['page'] += 1

    def get_courses(self, school_id, name=None, code=None):
        for course in self.get_pages(f'schools/{school_id}/courses'):
            if name is not None and course['name'] != name:
                continue
            if code is not None and course['code'] != code:
                continue
            yield course

    def get_assignments(self, course_id, name=None):
        for assignment in self.get_pages(f'courses/{course_id}/assignments'):
            if name is not None and assignment['name'] != name:
                continue
            yield assignment

    def get_result(self, result_id):
        response = self.get(f'results/{result_id}')
        return response.json()

    def get_results(self, assignment_id, status=None):
        for result in self.get_pages(f'assignments/{assignment_id}/results'):
            if status is not None and result['status'] != status:
                continue
            yield self.get_result(result['id'])

    def get_exercises(self, assignment_id):
        for exercise in self.get_pages(
            f'assignments/{assignment_id}/exercises'
        ):
            yield exercise

    def get_questions(self, exercise_id):
        for question in self.get_pages(f'exercises/{exercise_id}/questions'):
            yield question

    def post_comment(self, content, commentable_id, commentable_type):
        self.post(
            'comments',
            json={
                'content': content,
                'commentable_id': commentable_id,
                'commentable_type': commentable_type,
            }
        )

    def get_comments(self):
        return self.get_pages('comments')

    def delete_comment(self, comment_id):
        return self.delete(f'comments/{comment_id}')

    def get_submission(self, submission_id):
        response = self.get(f'submissions/{submission_id}')
        return response.json()
