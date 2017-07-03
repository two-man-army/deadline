import os


def create_task_test_files(task_tests_dir: str, test_number: int,
                           input: str, output: str):
    """
    Given a course name. lesson number and task number create the input/output files with the given input/output
    ex: education_tests/{course_name}/{lesson_number}/ - input_{task_number}.txt and output_{task_number}.txt
    """
    if not os.path.exists(task_tests_dir):
        os.makedirs(task_tests_dir)

    input_dir, output_dir = (os.path.join(task_tests_dir, f'input_{str(test_number).zfill(2)}.txt'),
                             os.path.join(task_tests_dir, f'output_{str(test_number).zfill(2)}.txt'))
    if os.path.isfile(input_dir) or os.path.isfile(output_dir):
        raise Exception(f'Input/output file #{test_number} in path {task_tests_dir} already exists!')

    with open(input_dir, 'w') as inp_f:
        inp_f.write(input)

    with open(output_dir, 'w') as outp_f:
        outp_f.write(output)

    return input_dir, output_dir
