import os
from constants import EDUCATION_TEST_FILES_FOLDER


def create_task_test_files(course_name: str, lesson_number: int,
                           task_number: int, input: str, output: str):
    """
    Given a course name. lesson number and task number create the input/output files with the given input/output
    ex: education_tests/{course_name}/{lesson_number}/ - input_{task_number}.txt and output_{task_number}.txt
    """
    lesson_tests_dir = os.path.join(
        os.path.join(EDUCATION_TEST_FILES_FOLDER, course_name),
        str(lesson_number)
    )
    if not os.path.exists(lesson_tests_dir):
        os.makedirs(lesson_tests_dir)

    input_dir, output_dir = (os.path.join(lesson_tests_dir, f'input_{str(task_number).zfill(2)}.txt'),
                             os.path.join(lesson_tests_dir, f'output_{str(task_number).zfill(2)}.txt'))
    if os.path.isfile(input_dir) or os.path.isfile(output_dir):
        raise Exception(f'Input/output file #{task_number} for course '
                        f'{course_name} lesson {lesson_number} already exists!')

    with open(input_dir, 'w') as inp_f:
        inp_f.write(input)

    with open(output_dir, 'w') as outp_f:
        outp_f.write(output)

