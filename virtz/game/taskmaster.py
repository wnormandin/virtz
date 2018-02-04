

from .models import Task

task_reference = {'task_name':{'property1':'value1'}}

class TaskMaster:

    ''' TaskMaster class for managing user-created tasks '''

    def __init__(self, task_queue):
        self.task_queue = task_queue

    def push_task(self, **kwargs):

        ''' Created a task and puts it into the task queue '''


