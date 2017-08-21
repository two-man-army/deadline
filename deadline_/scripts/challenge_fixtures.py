#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file has been automatically generated.
# Instead of changing it, create a file called import_helper.py
# and put there a class called ImportHelper(object) in it.
#
# This class will be specially casted so that instead of extending object,
# it will actually extend the class BasicImportHelper()
#
# That means you just have to overload the methods you want to
# change, leaving the other ones inteact.
#
# Something that you might want to do is use transactions, for example.
#
# Also, don't forget to add the necessary Django imports.
#
# This file was generated with the following command:
# manage.py dumpscript challenges
#
# to restore it, run
# manage.py runscript module_name.this_script_name
#
# example: if manage.py is at ./manage.py
# and the script is at ./some_folder/some_script.py
# you must make sure ./some_folder/__init__.py exists
# and run  ./manage.py runscript some_folder.some_script
import os, sys
from django.db import transaction

class BasicImportHelper(object):

    def pre_import(self):
        pass

    @transaction.atomic
    def run_import(self, import_data):
        import_data()

    def post_import(self):
        pass

    def locate_similar(self, current_object, search_data):
        # You will probably want to call this method from save_or_locate()
        # Example:
        #   new_obj = self.locate_similar(the_obj, {"national_id": the_obj.national_id } )

        the_obj = current_object.__class__.objects.get(**search_data)
        return the_obj

    def locate_object(self, original_class, original_pk_name, the_class, pk_name, pk_value, obj_content):
        # You may change this function to do specific lookup for specific objects
        #
        # original_class class of the django orm's object that needs to be located
        # original_pk_name the primary key of original_class
        # the_class      parent class of original_class which contains obj_content
        # pk_name        the primary key of original_class
        # pk_value       value of the primary_key
        # obj_content    content of the object which was not exported.
        #
        # You should use obj_content to locate the object on the target db
        #
        # An example where original_class and the_class are different is
        # when original_class is Farmer and the_class is Person. The table
        # may refer to a Farmer but you will actually need to locate Person
        # in order to instantiate that Farmer
        #
        # Example:
        #   if the_class == SurveyResultFormat or the_class == SurveyType or the_class == SurveyState:
        #       pk_name="name"
        #       pk_value=obj_content[pk_name]
        #   if the_class == StaffGroup:
        #       pk_value=8

        search_data = { pk_name: pk_value }
        the_obj = the_class.objects.get(**search_data)
        #print(the_obj)
        return the_obj


    def save_or_locate(self, the_obj):
        # Change this if you want to locate the object in the database
        try:
            the_obj.save()
        except:
            print("---------------")
            print("Error saving the following object:")
            print(the_obj.__class__)
            print(" ")
            print(the_obj.__dict__)
            print(" ")
            print(the_obj)
            print(" ")
            print("---------------")

            raise
        return the_obj


importer = None
try:
    import import_helper
    # We need this so ImportHelper can extend BasicImportHelper, although import_helper.py
    # has no knowlodge of this class
    importer = type("DynamicImportHelper", (import_helper.ImportHelper, BasicImportHelper ) , {} )()
except ImportError as e:
    # From Python 3.3 we can check e.name - string match is for backward compatibility.
    if 'import_helper' in str(e):
        importer = BasicImportHelper()
    else:
        raise

import datetime
from decimal import Decimal
from django.contrib.contenttypes.models import ContentType

try:
    import dateutil.parser
except ImportError:
    print("Please install python-dateutil")
    sys.exit(os.EX_USAGE)

def run():
    importer.pre_import()
    importer.run_import(import_data)
    importer.post_import()

def import_data():
    # Initial Imports

    # Processing model: challenges.models.Language

    from challenges.models import Language

    challenges_language_1 = Language()
    challenges_language_1.name = 'Python'
    challenges_language_1.default_code = "def main():\n    # Let's go champ\n    pass\n\nif __name__ == '__main__':\n    main()\n"
    challenges_language_1 = importer.save_or_locate(challenges_language_1)

    challenges_language_2 = Language()
    challenges_language_2.name = 'Go'
    challenges_language_2.default_code = 'package main\nimport "fmt"\n\nfunc main() {\n\t\n}'
    challenges_language_2 = importer.save_or_locate(challenges_language_2)

    challenges_language_3 = Language()
    challenges_language_3.name = 'Rust'
    challenges_language_3.default_code = 'use std::io;\n\nfn main() {\n\t\n}'
    challenges_language_3 = importer.save_or_locate(challenges_language_3)

    challenges_language_4 = Language()
    challenges_language_4.name = 'C++'
    challenges_language_4.default_code = '#include <iostream>\n\nuse std::cin;\nuse std::cout;\n\nint main() {\n\t\n\treturn 0;\n}'
    challenges_language_4 = importer.save_or_locate(challenges_language_4)

    challenges_language_5 = Language()
    challenges_language_5.name = 'Kotlin'
    challenges_language_5.default_code = 'import java.util.*\n\nfun main(args: Array<String>) {\n\t\n}'
    challenges_language_5 = importer.save_or_locate(challenges_language_5)

    challenges_language_6 = Language()
    challenges_language_6.name = 'Ruby'
    challenges_language_6.default_code = "# Let's go champ\n"
    challenges_language_6 = importer.save_or_locate(challenges_language_6)

    # Processing model: challenges.models.MainCategory

    from challenges.models import MainCategory

    challenges_maincategory_1 = MainCategory()
    challenges_maincategory_1.name = 'Algorithms'
    challenges_maincategory_1 = importer.save_or_locate(challenges_maincategory_1)

    challenges_maincategory_2 = MainCategory()
    challenges_maincategory_2.name = 'Data Structures'
    challenges_maincategory_2 = importer.save_or_locate(challenges_maincategory_2)

    challenges_maincategory_3 = MainCategory()
    challenges_maincategory_3.name = 'Python Language'
    challenges_maincategory_3 = importer.save_or_locate(challenges_maincategory_3)

    # Processing model: challenges.models.SubCategory

    from challenges.models import SubCategory

    challenges_subcategory_1 = SubCategory()
    challenges_subcategory_1.name = 'Introduction'
    challenges_subcategory_1.meta_category = challenges_maincategory_3
    challenges_subcategory_1.max_score = 0
    challenges_subcategory_1 = importer.save_or_locate(challenges_subcategory_1)

    challenges_subcategory_2 = SubCategory()
    challenges_subcategory_2.name = 'Collections'
    challenges_subcategory_2.meta_category = challenges_maincategory_3
    challenges_subcategory_2.max_score = 0
    challenges_subcategory_2 = importer.save_or_locate(challenges_subcategory_2)

    challenges_subcategory_3 = SubCategory()
    challenges_subcategory_3.name = 'Closures and Decorators'
    challenges_subcategory_3.meta_category = challenges_maincategory_3
    challenges_subcategory_3.max_score = 0
    challenges_subcategory_3 = importer.save_or_locate(challenges_subcategory_3)

    challenges_subcategory_4 = SubCategory()
    challenges_subcategory_4.name = 'Itertools'
    challenges_subcategory_4.meta_category = challenges_maincategory_3
    challenges_subcategory_4.max_score = 0
    challenges_subcategory_4 = importer.save_or_locate(challenges_subcategory_4)

    challenges_subcategory_5 = SubCategory()
    challenges_subcategory_5.name = 'Array'
    challenges_subcategory_5.meta_category = challenges_maincategory_2
    challenges_subcategory_5.max_score = 0
    challenges_subcategory_5 = importer.save_or_locate(challenges_subcategory_5)

    challenges_subcategory_6 = SubCategory()
    challenges_subcategory_6.name = 'Linked List'
    challenges_subcategory_6.meta_category = challenges_maincategory_2
    challenges_subcategory_6.max_score = 0
    challenges_subcategory_6 = importer.save_or_locate(challenges_subcategory_6)

    challenges_subcategory_7 = SubCategory()
    challenges_subcategory_7.name = 'Trees'
    challenges_subcategory_7.meta_category = challenges_maincategory_2
    challenges_subcategory_7.max_score = 0
    challenges_subcategory_7 = importer.save_or_locate(challenges_subcategory_7)

    challenges_subcategory_8 = SubCategory()
    challenges_subcategory_8.name = 'Disjoint Set'
    challenges_subcategory_8.meta_category = challenges_maincategory_2
    challenges_subcategory_8.max_score = 0
    challenges_subcategory_8 = importer.save_or_locate(challenges_subcategory_8)

    challenges_subcategory_9 = SubCategory()
    challenges_subcategory_9.name = 'Recursion'
    challenges_subcategory_9.meta_category = challenges_maincategory_1
    challenges_subcategory_9.max_score = 0
    challenges_subcategory_9 = importer.save_or_locate(challenges_subcategory_9)

    challenges_subcategory_10 = SubCategory()
    challenges_subcategory_10.name = 'Sorting'
    challenges_subcategory_10.meta_category = challenges_maincategory_1
    challenges_subcategory_10.max_score = 0
    challenges_subcategory_10 = importer.save_or_locate(challenges_subcategory_10)

    challenges_subcategory_11 = SubCategory()
    challenges_subcategory_11.name = 'Greedy'
    challenges_subcategory_11.meta_category = challenges_maincategory_1
    challenges_subcategory_11.max_score = 0
    challenges_subcategory_11 = importer.save_or_locate(challenges_subcategory_11)

    challenges_subcategory_12 = SubCategory()
    challenges_subcategory_12.name = 'Strings'
    challenges_subcategory_12.meta_category = challenges_maincategory_1
    challenges_subcategory_12.max_score = 0
    challenges_subcategory_12 = importer.save_or_locate(challenges_subcategory_12)

    challenges_subcategory_13 = SubCategory()
    challenges_subcategory_13.name = 'Graphs'
    challenges_subcategory_13.meta_category = challenges_maincategory_1
    challenges_subcategory_13.max_score = 0
    challenges_subcategory_13 = importer.save_or_locate(challenges_subcategory_13)

    challenges_subcategory_14 = SubCategory()
    challenges_subcategory_14.name = 'Dynamic Programming'
    challenges_subcategory_14.meta_category = challenges_maincategory_1
    challenges_subcategory_14.max_score = 0
    challenges_subcategory_14 = importer.save_or_locate(challenges_subcategory_14)

    challenges_subcategory_15 = SubCategory()
    challenges_subcategory_15.name = 'Miscellaneous'
    challenges_subcategory_15.meta_category = challenges_maincategory_1
    challenges_subcategory_15.max_score = 0
    challenges_subcategory_15 = importer.save_or_locate(challenges_subcategory_15)

    # Processing model: challenges.models.ChallengeDescription

    from challenges.models import ChallengeDescription

    challenges_challengedescription_1 = ChallengeDescription()
    challenges_challengedescription_1.content = 'Write a program that prints `Hello World` to the console!'
    challenges_challengedescription_1.input_format = ''
    challenges_challengedescription_1.output_format = 'The string "Hello World" on a single line.'
    challenges_challengedescription_1.constraints = ''
    challenges_challengedescription_1.sample_input = ''
    challenges_challengedescription_1.sample_output = ''
    challenges_challengedescription_1.explanation = ''
    challenges_challengedescription_1 = importer.save_or_locate(challenges_challengedescription_1)

    challenges_challengedescription_2 = ChallengeDescription()
    challenges_challengedescription_2.content = 'While studying for her university, FMI, Rositsa came up with the idea of a basic number.{{NPL}} {{NPL}}A basic number was the following: a positive number, which when represented in base **b** would have every prefix with **k** count digits(from 1 to the count of digits in the number to the given base) converted to base **b** be divisible by **k**. {{NPL}}{{NPL}}Example:{{NPL}}Using base 2{{NPL}}1 is a basic number since its prefix of length 1 (prefix=1) is divisible by 1{{NPL}}2 is a basic number. 2 in base 2 is 10, its prefix of length 1 is 1, which is divisible by 1 and its prefix of length 2 is 10, which is divisible by 2.{{NPL}}3, on the other hand, is not a basic number. Converted to base 2, 3 is equal to 11. Its prefix of length 1(prefix=1) is divisible by 1, but its prefix of length 2(prefix=11) is not divisible by 2.{{NPL}}{{NPL}}Rositsa wants you to find the count of basic numbers represented in the given base **b**, which are exactly **d** digits long (when converted to the base).'
    challenges_challengedescription_2.input_format = 'First line of the input denotes the number of test cases.{{NPL}}For each test case there is a single line containing two integers, the base **b** and digits **d**, separated by a single space.'
    challenges_challengedescription_2.output_format = 'A number on a single line'
    challenges_challengedescription_2.constraints = '1<=Test case count<=100{{NPL}}2<=Base<=4{{NPL}}1<=Digits<=10^7'
    challenges_challengedescription_2.sample_input = '{{NPL}}1{{NPL}}3 2'
    challenges_challengedescription_2.sample_output = '1'
    challenges_challengedescription_2.explanation = 'There are exactly 6 numbers that have 2 digits converted to base 3 and they are [3, 4, 5, 6, 7, 8](in base 3 [10, 11, 12, 20, 21, 22]) {{NPL}}Only numbers 4(11), 6(20) and 8(22) are basic numbers. 4 is a basic number, because his prefix of length 1(prefix=1, converted to base 3=1) is divisible by 1 and its prefix of length 2(prefix=11, converted to base3=4) is divisible by 2.'
    challenges_challengedescription_2 = importer.save_or_locate(challenges_challengedescription_2)

    challenges_challengedescription_3 = ChallengeDescription()
    challenges_challengedescription_3.content = 'Given an a list of **N** numbers, find their sum'
    challenges_challengedescription_3.input_format = 'One line, containing the numbers, separated by a comma and whitespace'
    challenges_challengedescription_3.output_format = 'A number on a single line, the sum of the numbers'
    challenges_challengedescription_3.constraints = '1<=Number<=100000{{NPL}}1<=N<=1000'
    challenges_challengedescription_3.sample_input = '1, 2, 3'
    challenges_challengedescription_3.sample_output = '6'
    challenges_challengedescription_3.explanation = '1 + 2 + 3 = 6'
    challenges_challengedescription_3 = importer.save_or_locate(challenges_challengedescription_3)

    challenges_challengedescription_4 = ChallengeDescription()
    challenges_challengedescription_4.content = 'Given a sequence of numbers, find the smallest and biggest number in said sequence.'
    challenges_challengedescription_4.input_format = 'One line, containing the numbers, separated by a comma and whitespace'
    challenges_challengedescription_4.output_format = 'The smallest and biggest number printed on a single line, separated by a comma'
    challenges_challengedescription_4.constraints = '1<=Number<=100000{{NPL}}1<=N<=1000'
    challenges_challengedescription_4.sample_input = '10, 12, -1'
    challenges_challengedescription_4.sample_output = '-1, 12'
    challenges_challengedescription_4.explanation = ''
    challenges_challengedescription_4 = importer.save_or_locate(challenges_challengedescription_4)

    challenges_challengedescription_5 = ChallengeDescription()
    challenges_challengedescription_5.content = "Mark and Emily are the only people that managed to survive the apocalypse that 2048 brought with it. Unfortunately for them, the apocalypse split the Earth into islands separated by lava. {{NPL}}Given the Earth's map in a Cartesian coordinate system and the coordinates of each island, your job is to say whether Mark and Emily will ever be able to meet through land."
    challenges_challengedescription_5.input_format = 'On the first input line you will be given the number of islands **N** and the number of queries **M** as 2 space-separated integers.{{NPL}}On the next **N** lines you will be given the coordinates of each log in the format " **Ax** **Ay** **Bx** **By** ".{{NPL}}On the next **M** lines you will be given queries in the format "A B" where A and B correspond to the island Mark and Emily are on respectively, in the order they were given in the input (starting from 1).'
    challenges_challengedescription_5.output_format = 'For each query print "**YES**" if the their islands are connected. Otherwise, print "**NO**".'
    challenges_challengedescription_5.constraints = '2<=N<=1000{{NPL}}1<=M<=10000{{NPL}}All island coordinates will be valid integer numbers in the range [-100..100].'
    challenges_challengedescription_5.sample_input = '4 3{{NPL}}-35 60 -20 15{{NPL}}-50 20 -30 -20{{NPL}}-10 30 60 10{{NPL}}-40 -10 50 -30{{NPL}}2 4{{NPL}}4 3{{NPL}}4 1'
    challenges_challengedescription_5.sample_output = 'YES{{NPL}}YES{{NPL}}NO'
    challenges_challengedescription_5.explanation = 'Islands 1->2->4 are connected and Island 3 is not connected to anything.'
    challenges_challengedescription_5 = importer.save_or_locate(challenges_challengedescription_5)

    challenges_challengedescription_6 = ChallengeDescription()
    challenges_challengedescription_6.content = 'Solomon is out on an adventure in a labyrinth. The purpose of a labyrinth is to find the way out, but Solomon is rather strange and enjoys his time in the labyrinth. Only being able to move left, right, up and down, he wants you to find the longest path in the labyrinth for him, so that he can walk the maximum distance before exiting. {{NPL}}The labyrinth will be represented by non-distinct integers in a matrix. A valid path through the labyrinth is defined as a path where the number Solomon steps on is increased by 1 exactly.{{NPL}}Example: 1->2->3 is a valid path, but 1->3->4 is not.'
    challenges_challengedescription_6.input_format = 'On the first input line you will be given the number of rows **N** and the number of columns **M** as 2 space-separated integers.{{NPL}}On the next **N** lines you will be given all the numbers on that row, separated by a single space.'
    challenges_challengedescription_6.output_format = 'On the first line, print the number of steps that Solomon will walk on the longest path.{{NPL}}On the second line, print the numbers that Solomon has stepped on his path in consecutive order.{{NPL}}Prioritize going in the following directions all the time: LEFT, RIGHT, DOWN, UP.'
    challenges_challengedescription_6.constraints = '2<=N<=1000{{NPL}}1<=M<=1000'
    challenges_challengedescription_6.sample_input = '3 4{{NPL}}1 2 3 14{{NPL}}2 1 2 3{{NPL}}3 4 5 4'
    challenges_challengedescription_6.sample_output = '5{{NPL}}1->2->3->4->5'
    challenges_challengedescription_6.explanation = 'There are two identical best paths.{{NPL}}The first one start at 0,0, goes all the way down and right until it reaches 5.{{NPL}}The second one starts at 1,2, goes all the way right, down once and left to reach the 5.'
    challenges_challengedescription_6 = importer.save_or_locate(challenges_challengedescription_6)

    challenges_challengedescription_7 = ChallengeDescription()
    challenges_challengedescription_7.content = 'Joe has decided it is time to mow his **N**x**M** lawn, although before he starts off, he wants to know how much time it will take him.{{NPL}}He knows how much seconds each square meter will take him, but is not good enough to calculate the overall time.{{NPL}}Joe will also ask you for **T** various land areas to find one that will take exactly as much time as he wants to spend today.{{NPL}}For each single land area, Joe will give you (**i**, **j**) the top-left and (**k**, **l**) bottom-right point coordinates and will expect you to tell him the amount of seconds it will take him to mow that lawn area.'
    challenges_challengedescription_7.input_format = "On the first line, you will receive **N** and **M** indicating the lawn's height and width, respectively{{NPL}}On the second line, you will receive **T**, the count of land areas Joe will ask for{{NPL}}For **N** more lines, you will receive **M** space separated integers, denoting the seconds required to mow the square meter at that line.{{NPL}}For **T** more lines, you will receive **i**, **j**, **k**, and **ll**, denoting the top-left and bottom-right points of the area Joe is asking for."
    challenges_challengedescription_7.output_format = 'For each **T** area, output a single integer denoting the sum of the seconds in all cells that fall withing the given area.'
    challenges_challengedescription_7.constraints = '1 <= **N** <= 2500{{NPL}}1 <= **M** <= 2500{{NPL}}5 <= **T** <= 25000'
    challenges_challengedescription_7.sample_input = '4 4{{NPL}}2{{NPL}}3 0 1 4{{NPL}}5 6 3 2{{NPL}}1 2 0 1{{NPL}}4 1 0 1{{NPL}}2 2 3 3{{NPL}}0 0 1 2'
    challenges_challengedescription_7.sample_output = '4{{NPL}}18'
    challenges_challengedescription_7.explanation = ''
    challenges_challengedescription_7 = importer.save_or_locate(challenges_challengedescription_7)

    challenges_challengedescription_8 = ChallengeDescription()
    challenges_challengedescription_8.content = "Rodger is preparing for the greatest tennis competition of all time. Although, to qualify for it, he needs to accumulate points from other contests. {{NPL}}Tennis contests are either ranked or unranked. {{NPL}}Rodger knows for a fact that out of all the ranked competitions, he will win K of them. (for the rest, he plays it safe and assumes he'll lose). Lost contests will take away points from him! {{NPL}}For the unranked competitions, Rodger is confident he will win all of them, as he is really skilled.{{NPL}}Given all the upcoming competitions, figure out the maximum amount of points Rodger can accumulate, given the constraints above."
    challenges_challengedescription_8.input_format = 'The first line contains two space-separated integers, **N** (the number of contests) and **K** (the number of ranked contests Rodger will win){{NPL}}{{NPL}}Each line of the **N** subsequent lines contain two space-separated integers, **P** (the contests points awarded for winning) and **IMP** (0 or 1, denoting if the contest is important or not)'
    challenges_challengedescription_8.output_format = 'Print a single integer denoting the maximum amount of points Rodger can accumulate while taking the constraints into account'
    challenges_challengedescription_8.constraints = '1 <= **N** <= 20000{{NPL}}1 <= **K** <= **N** {{NPL}}1 <= **P** <= 200'
    challenges_challengedescription_8.sample_input = ''
    challenges_challengedescription_8.sample_output = ''
    challenges_challengedescription_8.explanation = ''
    challenges_challengedescription_8 = importer.save_or_locate(challenges_challengedescription_8)

    challenges_challengedescription_9 = ChallengeDescription()
    challenges_challengedescription_9.content = 'Jim owns the company UpSum, whose job is to constantly calculate sums. Today a new client presented themselves to UpSum and they wanted a similar service - one for multiplication. UpSum did not have any employees who could do the job and that is why they posted on Deadline in the hopes of having some skilled worker solve their problem. {{NPL}} The client wants, with the presence of a number **N** and a list of possible multipliers **MP**, to get the trail with which they got to the number **N**. {{NPL}} As multiple such trails exist, the client wants the lexicographically smallest one. {{NPL}}This is best explained with an example as follows:{{NPL}}Given **N** = 24 and **MP** = [2, 3, 4], then the following ways exist:{{NPL}}{{NPL}}1 (*3) = 3 (*4) = 12 (*2) = 24. [1, 3, 12, 24]{{NPL}}1 (*4) = 4 (*2) = 8 (*3) = 24. [1, 4, 8, 24]{{NPL}}1 (*2) = 2 (*2) = 4 (*2) = 8 (*3) = 24. [1, 2, 4, 8]{{NPL}}1 (*2) = 2 (*3) = 6 (*4) = 24 [1, 2, 6, 24]{{NPL}}{{NPL}}Others might also exist, but out of the four given, the fourth one is the smallest collection lexicographically.{{NPL}}If there is no way to reach **N** starting from 1, simply output -1.'
    challenges_challengedescription_9.input_format = 'The first line contains two space separated integers, **N** and **M**, respectively denoting the number we want to reach and the amount of multipliers in the **MP** list.{{NPL}}The second line contains **M** space separated integers, denoting the **MP** collecion.'
    challenges_challengedescription_9.output_format = 'Output a single line of spare separated integers, denoting the legicographically smallest path to reaching **N** from the number 1.{{NPL}}In case no such exists, output -1'
    challenges_challengedescription_9.constraints = '1 <= **N** <= 1000000000{{NPL}}1 <= **MP** <= 21000{{NPL}}1 <= **MP** element <= Sqrt( **N** )'
    challenges_challengedescription_9.sample_input = ''
    challenges_challengedescription_9.sample_output = ''
    challenges_challengedescription_9.explanation = ''
    challenges_challengedescription_9 = importer.save_or_locate(challenges_challengedescription_9)

    challenges_challengedescription_10 = ChallengeDescription()
    challenges_challengedescription_10.content = "You have a pile of **P** toys that you want to split into multiple piles, as well as a list of positive integers **L** .{{NPL}}We define a split as follows:{{NPL}}    First, choose a pile of toys. Let's say the chosen pile contains **y** toys{{NPL}}    Next, look for some number **x** that is in **L** , is not equal to **y** and **y** is divisible by **x** . If such an **x** exists, you can split the pile into y/x equal smaller piles.{{NPL}}For the given pile, calculate the maximum possible number of moves you can perform and print it on a new line."
    challenges_challengedescription_10.input_format = 'First line contains two space separated integers,{{NPL}}    **P** - the number of toys in the initial pile{{NPL}}    **k** - the count of numbers in **L**{{NPL}}Second line contains **k** space separated positive integers, denoting **L**'
    challenges_challengedescription_10.output_format = 'Output a single integer, denoting the maximum amount of splits possible for the given pile'
    challenges_challengedescription_10.constraints = '1 <= **P** <= 10^9{{NPL}}1 <= **k** <= 20000'
    challenges_challengedescription_10.sample_input = '12 2{{NPL}}3 6{{NPL}}3'
    challenges_challengedescription_10.sample_output = '3'
    challenges_challengedescription_10.explanation = 'We split 12 by 3 equalling 2 piles of size 6. We split both piles separately with 3, equalling 4 piles of size 3. {{NPL}In total: 3 splits.'
    challenges_challengedescription_10 = importer.save_or_locate(challenges_challengedescription_10)

    # Processing model: challenges.models.Proficiency

    from challenges.models import Proficiency

    challenges_proficiency_1 = Proficiency()
    challenges_proficiency_1.name = ''
    challenges_proficiency_1.needed_percentage = 0
    challenges_proficiency_1 = importer.save_or_locate(challenges_proficiency_1)

    challenges_proficiency_2 = Proficiency()
    challenges_proficiency_2.name = 'Novice'
    challenges_proficiency_2.needed_percentage = 20
    challenges_proficiency_2 = importer.save_or_locate(challenges_proficiency_2)

    challenges_proficiency_3 = Proficiency()
    challenges_proficiency_3.name = 'Intermediate'
    challenges_proficiency_3.needed_percentage = 45
    challenges_proficiency_3 = importer.save_or_locate(challenges_proficiency_3)

    challenges_proficiency_4 = Proficiency()
    challenges_proficiency_4.name = 'Experienced'
    challenges_proficiency_4.needed_percentage = 70
    challenges_proficiency_4 = importer.save_or_locate(challenges_proficiency_4)

    challenges_proficiency_5 = Proficiency()
    challenges_proficiency_5.name = 'Advanced'
    challenges_proficiency_5.needed_percentage = 95
    challenges_proficiency_5 = importer.save_or_locate(challenges_proficiency_5)

    # Processing model: challenges.models.UserSubcategoryProficiency

    from challenges.models import UserSubcategoryProficiency


    # Processing model: challenges.models.SubcategoryProficiencyAward

    from challenges.models import SubcategoryProficiencyAward

    challenges_subcategoryproficiencyaward_1 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_1.subcategory = challenges_subcategory_1
    challenges_subcategoryproficiencyaward_1.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_1.xp_reward = 112
    challenges_subcategoryproficiencyaward_1 = importer.save_or_locate(challenges_subcategoryproficiencyaward_1)

    challenges_subcategoryproficiencyaward_2 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_2.subcategory = challenges_subcategory_1
    challenges_subcategoryproficiencyaward_2.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_2.xp_reward = 1001
    challenges_subcategoryproficiencyaward_2 = importer.save_or_locate(challenges_subcategoryproficiencyaward_2)

    challenges_subcategoryproficiencyaward_3 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_3.subcategory = challenges_subcategory_1
    challenges_subcategoryproficiencyaward_3.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_3.xp_reward = 2001
    challenges_subcategoryproficiencyaward_3 = importer.save_or_locate(challenges_subcategoryproficiencyaward_3)

    challenges_subcategoryproficiencyaward_4 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_4.subcategory = challenges_subcategory_1
    challenges_subcategoryproficiencyaward_4.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_4.xp_reward = 3001
    challenges_subcategoryproficiencyaward_4 = importer.save_or_locate(challenges_subcategoryproficiencyaward_4)

    challenges_subcategoryproficiencyaward_5 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_5.subcategory = challenges_subcategory_1
    challenges_subcategoryproficiencyaward_5.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_5.xp_reward = 4001
    challenges_subcategoryproficiencyaward_5 = importer.save_or_locate(challenges_subcategoryproficiencyaward_5)

    challenges_subcategoryproficiencyaward_6 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_6.subcategory = challenges_subcategory_2
    challenges_subcategoryproficiencyaward_6.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_6.xp_reward = 112
    challenges_subcategoryproficiencyaward_6 = importer.save_or_locate(challenges_subcategoryproficiencyaward_6)

    challenges_subcategoryproficiencyaward_7 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_7.subcategory = challenges_subcategory_2
    challenges_subcategoryproficiencyaward_7.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_7.xp_reward = 1001
    challenges_subcategoryproficiencyaward_7 = importer.save_or_locate(challenges_subcategoryproficiencyaward_7)

    challenges_subcategoryproficiencyaward_8 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_8.subcategory = challenges_subcategory_2
    challenges_subcategoryproficiencyaward_8.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_8.xp_reward = 2001
    challenges_subcategoryproficiencyaward_8 = importer.save_or_locate(challenges_subcategoryproficiencyaward_8)

    challenges_subcategoryproficiencyaward_9 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_9.subcategory = challenges_subcategory_2
    challenges_subcategoryproficiencyaward_9.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_9.xp_reward = 3001
    challenges_subcategoryproficiencyaward_9 = importer.save_or_locate(challenges_subcategoryproficiencyaward_9)

    challenges_subcategoryproficiencyaward_10 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_10.subcategory = challenges_subcategory_2
    challenges_subcategoryproficiencyaward_10.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_10.xp_reward = 4001
    challenges_subcategoryproficiencyaward_10 = importer.save_or_locate(challenges_subcategoryproficiencyaward_10)

    challenges_subcategoryproficiencyaward_11 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_11.subcategory = challenges_subcategory_3
    challenges_subcategoryproficiencyaward_11.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_11.xp_reward = 112
    challenges_subcategoryproficiencyaward_11 = importer.save_or_locate(challenges_subcategoryproficiencyaward_11)

    challenges_subcategoryproficiencyaward_12 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_12.subcategory = challenges_subcategory_3
    challenges_subcategoryproficiencyaward_12.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_12.xp_reward = 1001
    challenges_subcategoryproficiencyaward_12 = importer.save_or_locate(challenges_subcategoryproficiencyaward_12)

    challenges_subcategoryproficiencyaward_13 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_13.subcategory = challenges_subcategory_3
    challenges_subcategoryproficiencyaward_13.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_13.xp_reward = 2001
    challenges_subcategoryproficiencyaward_13 = importer.save_or_locate(challenges_subcategoryproficiencyaward_13)

    challenges_subcategoryproficiencyaward_14 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_14.subcategory = challenges_subcategory_3
    challenges_subcategoryproficiencyaward_14.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_14.xp_reward = 3001
    challenges_subcategoryproficiencyaward_14 = importer.save_or_locate(challenges_subcategoryproficiencyaward_14)

    challenges_subcategoryproficiencyaward_15 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_15.subcategory = challenges_subcategory_3
    challenges_subcategoryproficiencyaward_15.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_15.xp_reward = 4001
    challenges_subcategoryproficiencyaward_15 = importer.save_or_locate(challenges_subcategoryproficiencyaward_15)

    challenges_subcategoryproficiencyaward_16 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_16.subcategory = challenges_subcategory_4
    challenges_subcategoryproficiencyaward_16.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_16.xp_reward = 112
    challenges_subcategoryproficiencyaward_16 = importer.save_or_locate(challenges_subcategoryproficiencyaward_16)

    challenges_subcategoryproficiencyaward_17 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_17.subcategory = challenges_subcategory_4
    challenges_subcategoryproficiencyaward_17.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_17.xp_reward = 1001
    challenges_subcategoryproficiencyaward_17 = importer.save_or_locate(challenges_subcategoryproficiencyaward_17)

    challenges_subcategoryproficiencyaward_18 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_18.subcategory = challenges_subcategory_4
    challenges_subcategoryproficiencyaward_18.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_18.xp_reward = 2001
    challenges_subcategoryproficiencyaward_18 = importer.save_or_locate(challenges_subcategoryproficiencyaward_18)

    challenges_subcategoryproficiencyaward_19 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_19.subcategory = challenges_subcategory_4
    challenges_subcategoryproficiencyaward_19.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_19.xp_reward = 3001
    challenges_subcategoryproficiencyaward_19 = importer.save_or_locate(challenges_subcategoryproficiencyaward_19)

    challenges_subcategoryproficiencyaward_20 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_20.subcategory = challenges_subcategory_4
    challenges_subcategoryproficiencyaward_20.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_20.xp_reward = 4001
    challenges_subcategoryproficiencyaward_20 = importer.save_or_locate(challenges_subcategoryproficiencyaward_20)

    challenges_subcategoryproficiencyaward_21 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_21.subcategory = challenges_subcategory_5
    challenges_subcategoryproficiencyaward_21.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_21.xp_reward = 112
    challenges_subcategoryproficiencyaward_21 = importer.save_or_locate(challenges_subcategoryproficiencyaward_21)

    challenges_subcategoryproficiencyaward_22 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_22.subcategory = challenges_subcategory_5
    challenges_subcategoryproficiencyaward_22.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_22.xp_reward = 1001
    challenges_subcategoryproficiencyaward_22 = importer.save_or_locate(challenges_subcategoryproficiencyaward_22)

    challenges_subcategoryproficiencyaward_23 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_23.subcategory = challenges_subcategory_5
    challenges_subcategoryproficiencyaward_23.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_23.xp_reward = 2001
    challenges_subcategoryproficiencyaward_23 = importer.save_or_locate(challenges_subcategoryproficiencyaward_23)

    challenges_subcategoryproficiencyaward_24 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_24.subcategory = challenges_subcategory_5
    challenges_subcategoryproficiencyaward_24.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_24.xp_reward = 3001
    challenges_subcategoryproficiencyaward_24 = importer.save_or_locate(challenges_subcategoryproficiencyaward_24)

    challenges_subcategoryproficiencyaward_25 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_25.subcategory = challenges_subcategory_5
    challenges_subcategoryproficiencyaward_25.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_25.xp_reward = 4001
    challenges_subcategoryproficiencyaward_25 = importer.save_or_locate(challenges_subcategoryproficiencyaward_25)

    challenges_subcategoryproficiencyaward_26 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_26.subcategory = challenges_subcategory_6
    challenges_subcategoryproficiencyaward_26.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_26.xp_reward = 112
    challenges_subcategoryproficiencyaward_26 = importer.save_or_locate(challenges_subcategoryproficiencyaward_26)

    challenges_subcategoryproficiencyaward_27 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_27.subcategory = challenges_subcategory_6
    challenges_subcategoryproficiencyaward_27.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_27.xp_reward = 1001
    challenges_subcategoryproficiencyaward_27 = importer.save_or_locate(challenges_subcategoryproficiencyaward_27)

    challenges_subcategoryproficiencyaward_28 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_28.subcategory = challenges_subcategory_6
    challenges_subcategoryproficiencyaward_28.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_28.xp_reward = 2001
    challenges_subcategoryproficiencyaward_28 = importer.save_or_locate(challenges_subcategoryproficiencyaward_28)

    challenges_subcategoryproficiencyaward_29 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_29.subcategory = challenges_subcategory_6
    challenges_subcategoryproficiencyaward_29.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_29.xp_reward = 3001
    challenges_subcategoryproficiencyaward_29 = importer.save_or_locate(challenges_subcategoryproficiencyaward_29)

    challenges_subcategoryproficiencyaward_30 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_30.subcategory = challenges_subcategory_6
    challenges_subcategoryproficiencyaward_30.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_30.xp_reward = 4001
    challenges_subcategoryproficiencyaward_30 = importer.save_or_locate(challenges_subcategoryproficiencyaward_30)

    challenges_subcategoryproficiencyaward_31 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_31.subcategory = challenges_subcategory_7
    challenges_subcategoryproficiencyaward_31.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_31.xp_reward = 112
    challenges_subcategoryproficiencyaward_31 = importer.save_or_locate(challenges_subcategoryproficiencyaward_31)

    challenges_subcategoryproficiencyaward_32 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_32.subcategory = challenges_subcategory_7
    challenges_subcategoryproficiencyaward_32.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_32.xp_reward = 1001
    challenges_subcategoryproficiencyaward_32 = importer.save_or_locate(challenges_subcategoryproficiencyaward_32)

    challenges_subcategoryproficiencyaward_33 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_33.subcategory = challenges_subcategory_7
    challenges_subcategoryproficiencyaward_33.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_33.xp_reward = 2001
    challenges_subcategoryproficiencyaward_33 = importer.save_or_locate(challenges_subcategoryproficiencyaward_33)

    challenges_subcategoryproficiencyaward_34 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_34.subcategory = challenges_subcategory_7
    challenges_subcategoryproficiencyaward_34.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_34.xp_reward = 3001
    challenges_subcategoryproficiencyaward_34 = importer.save_or_locate(challenges_subcategoryproficiencyaward_34)

    challenges_subcategoryproficiencyaward_35 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_35.subcategory = challenges_subcategory_7
    challenges_subcategoryproficiencyaward_35.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_35.xp_reward = 4001
    challenges_subcategoryproficiencyaward_35 = importer.save_or_locate(challenges_subcategoryproficiencyaward_35)

    challenges_subcategoryproficiencyaward_36 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_36.subcategory = challenges_subcategory_8
    challenges_subcategoryproficiencyaward_36.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_36.xp_reward = 112
    challenges_subcategoryproficiencyaward_36 = importer.save_or_locate(challenges_subcategoryproficiencyaward_36)

    challenges_subcategoryproficiencyaward_37 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_37.subcategory = challenges_subcategory_8
    challenges_subcategoryproficiencyaward_37.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_37.xp_reward = 1001
    challenges_subcategoryproficiencyaward_37 = importer.save_or_locate(challenges_subcategoryproficiencyaward_37)

    challenges_subcategoryproficiencyaward_38 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_38.subcategory = challenges_subcategory_8
    challenges_subcategoryproficiencyaward_38.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_38.xp_reward = 2001
    challenges_subcategoryproficiencyaward_38 = importer.save_or_locate(challenges_subcategoryproficiencyaward_38)

    challenges_subcategoryproficiencyaward_39 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_39.subcategory = challenges_subcategory_8
    challenges_subcategoryproficiencyaward_39.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_39.xp_reward = 3001
    challenges_subcategoryproficiencyaward_39 = importer.save_or_locate(challenges_subcategoryproficiencyaward_39)

    challenges_subcategoryproficiencyaward_40 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_40.subcategory = challenges_subcategory_8
    challenges_subcategoryproficiencyaward_40.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_40.xp_reward = 4001
    challenges_subcategoryproficiencyaward_40 = importer.save_or_locate(challenges_subcategoryproficiencyaward_40)

    challenges_subcategoryproficiencyaward_41 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_41.subcategory = challenges_subcategory_9
    challenges_subcategoryproficiencyaward_41.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_41.xp_reward = 112
    challenges_subcategoryproficiencyaward_41 = importer.save_or_locate(challenges_subcategoryproficiencyaward_41)

    challenges_subcategoryproficiencyaward_42 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_42.subcategory = challenges_subcategory_9
    challenges_subcategoryproficiencyaward_42.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_42.xp_reward = 1001
    challenges_subcategoryproficiencyaward_42 = importer.save_or_locate(challenges_subcategoryproficiencyaward_42)

    challenges_subcategoryproficiencyaward_43 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_43.subcategory = challenges_subcategory_9
    challenges_subcategoryproficiencyaward_43.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_43.xp_reward = 2001
    challenges_subcategoryproficiencyaward_43 = importer.save_or_locate(challenges_subcategoryproficiencyaward_43)

    challenges_subcategoryproficiencyaward_44 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_44.subcategory = challenges_subcategory_9
    challenges_subcategoryproficiencyaward_44.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_44.xp_reward = 3001
    challenges_subcategoryproficiencyaward_44 = importer.save_or_locate(challenges_subcategoryproficiencyaward_44)

    challenges_subcategoryproficiencyaward_45 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_45.subcategory = challenges_subcategory_9
    challenges_subcategoryproficiencyaward_45.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_45.xp_reward = 4001
    challenges_subcategoryproficiencyaward_45 = importer.save_or_locate(challenges_subcategoryproficiencyaward_45)

    challenges_subcategoryproficiencyaward_46 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_46.subcategory = challenges_subcategory_10
    challenges_subcategoryproficiencyaward_46.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_46.xp_reward = 112
    challenges_subcategoryproficiencyaward_46 = importer.save_or_locate(challenges_subcategoryproficiencyaward_46)

    challenges_subcategoryproficiencyaward_47 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_47.subcategory = challenges_subcategory_10
    challenges_subcategoryproficiencyaward_47.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_47.xp_reward = 1001
    challenges_subcategoryproficiencyaward_47 = importer.save_or_locate(challenges_subcategoryproficiencyaward_47)

    challenges_subcategoryproficiencyaward_48 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_48.subcategory = challenges_subcategory_10
    challenges_subcategoryproficiencyaward_48.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_48.xp_reward = 2001
    challenges_subcategoryproficiencyaward_48 = importer.save_or_locate(challenges_subcategoryproficiencyaward_48)

    challenges_subcategoryproficiencyaward_49 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_49.subcategory = challenges_subcategory_10
    challenges_subcategoryproficiencyaward_49.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_49.xp_reward = 3001
    challenges_subcategoryproficiencyaward_49 = importer.save_or_locate(challenges_subcategoryproficiencyaward_49)

    challenges_subcategoryproficiencyaward_50 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_50.subcategory = challenges_subcategory_10
    challenges_subcategoryproficiencyaward_50.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_50.xp_reward = 4001
    challenges_subcategoryproficiencyaward_50 = importer.save_or_locate(challenges_subcategoryproficiencyaward_50)

    challenges_subcategoryproficiencyaward_51 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_51.subcategory = challenges_subcategory_11
    challenges_subcategoryproficiencyaward_51.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_51.xp_reward = 112
    challenges_subcategoryproficiencyaward_51 = importer.save_or_locate(challenges_subcategoryproficiencyaward_51)

    challenges_subcategoryproficiencyaward_52 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_52.subcategory = challenges_subcategory_11
    challenges_subcategoryproficiencyaward_52.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_52.xp_reward = 1001
    challenges_subcategoryproficiencyaward_52 = importer.save_or_locate(challenges_subcategoryproficiencyaward_52)

    challenges_subcategoryproficiencyaward_53 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_53.subcategory = challenges_subcategory_11
    challenges_subcategoryproficiencyaward_53.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_53.xp_reward = 2001
    challenges_subcategoryproficiencyaward_53 = importer.save_or_locate(challenges_subcategoryproficiencyaward_53)

    challenges_subcategoryproficiencyaward_54 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_54.subcategory = challenges_subcategory_11
    challenges_subcategoryproficiencyaward_54.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_54.xp_reward = 3001
    challenges_subcategoryproficiencyaward_54 = importer.save_or_locate(challenges_subcategoryproficiencyaward_54)

    challenges_subcategoryproficiencyaward_55 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_55.subcategory = challenges_subcategory_11
    challenges_subcategoryproficiencyaward_55.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_55.xp_reward = 4001
    challenges_subcategoryproficiencyaward_55 = importer.save_or_locate(challenges_subcategoryproficiencyaward_55)

    challenges_subcategoryproficiencyaward_56 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_56.subcategory = challenges_subcategory_12
    challenges_subcategoryproficiencyaward_56.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_56.xp_reward = 112
    challenges_subcategoryproficiencyaward_56 = importer.save_or_locate(challenges_subcategoryproficiencyaward_56)

    challenges_subcategoryproficiencyaward_57 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_57.subcategory = challenges_subcategory_12
    challenges_subcategoryproficiencyaward_57.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_57.xp_reward = 1001
    challenges_subcategoryproficiencyaward_57 = importer.save_or_locate(challenges_subcategoryproficiencyaward_57)

    challenges_subcategoryproficiencyaward_58 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_58.subcategory = challenges_subcategory_12
    challenges_subcategoryproficiencyaward_58.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_58.xp_reward = 2001
    challenges_subcategoryproficiencyaward_58 = importer.save_or_locate(challenges_subcategoryproficiencyaward_58)

    challenges_subcategoryproficiencyaward_59 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_59.subcategory = challenges_subcategory_12
    challenges_subcategoryproficiencyaward_59.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_59.xp_reward = 3001
    challenges_subcategoryproficiencyaward_59 = importer.save_or_locate(challenges_subcategoryproficiencyaward_59)

    challenges_subcategoryproficiencyaward_60 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_60.subcategory = challenges_subcategory_12
    challenges_subcategoryproficiencyaward_60.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_60.xp_reward = 4001
    challenges_subcategoryproficiencyaward_60 = importer.save_or_locate(challenges_subcategoryproficiencyaward_60)

    challenges_subcategoryproficiencyaward_61 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_61.subcategory = challenges_subcategory_13
    challenges_subcategoryproficiencyaward_61.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_61.xp_reward = 112
    challenges_subcategoryproficiencyaward_61 = importer.save_or_locate(challenges_subcategoryproficiencyaward_61)

    challenges_subcategoryproficiencyaward_62 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_62.subcategory = challenges_subcategory_13
    challenges_subcategoryproficiencyaward_62.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_62.xp_reward = 1001
    challenges_subcategoryproficiencyaward_62 = importer.save_or_locate(challenges_subcategoryproficiencyaward_62)

    challenges_subcategoryproficiencyaward_63 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_63.subcategory = challenges_subcategory_13
    challenges_subcategoryproficiencyaward_63.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_63.xp_reward = 2001
    challenges_subcategoryproficiencyaward_63 = importer.save_or_locate(challenges_subcategoryproficiencyaward_63)

    challenges_subcategoryproficiencyaward_64 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_64.subcategory = challenges_subcategory_13
    challenges_subcategoryproficiencyaward_64.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_64.xp_reward = 3001
    challenges_subcategoryproficiencyaward_64 = importer.save_or_locate(challenges_subcategoryproficiencyaward_64)

    challenges_subcategoryproficiencyaward_65 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_65.subcategory = challenges_subcategory_13
    challenges_subcategoryproficiencyaward_65.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_65.xp_reward = 4001
    challenges_subcategoryproficiencyaward_65 = importer.save_or_locate(challenges_subcategoryproficiencyaward_65)

    challenges_subcategoryproficiencyaward_66 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_66.subcategory = challenges_subcategory_14
    challenges_subcategoryproficiencyaward_66.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_66.xp_reward = 112
    challenges_subcategoryproficiencyaward_66 = importer.save_or_locate(challenges_subcategoryproficiencyaward_66)

    challenges_subcategoryproficiencyaward_67 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_67.subcategory = challenges_subcategory_14
    challenges_subcategoryproficiencyaward_67.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_67.xp_reward = 1001
    challenges_subcategoryproficiencyaward_67 = importer.save_or_locate(challenges_subcategoryproficiencyaward_67)

    challenges_subcategoryproficiencyaward_68 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_68.subcategory = challenges_subcategory_14
    challenges_subcategoryproficiencyaward_68.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_68.xp_reward = 2001
    challenges_subcategoryproficiencyaward_68 = importer.save_or_locate(challenges_subcategoryproficiencyaward_68)

    challenges_subcategoryproficiencyaward_69 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_69.subcategory = challenges_subcategory_14
    challenges_subcategoryproficiencyaward_69.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_69.xp_reward = 3001
    challenges_subcategoryproficiencyaward_69 = importer.save_or_locate(challenges_subcategoryproficiencyaward_69)

    challenges_subcategoryproficiencyaward_70 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_70.subcategory = challenges_subcategory_14
    challenges_subcategoryproficiencyaward_70.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_70.xp_reward = 4001
    challenges_subcategoryproficiencyaward_70 = importer.save_or_locate(challenges_subcategoryproficiencyaward_70)

    challenges_subcategoryproficiencyaward_71 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_71.subcategory = challenges_subcategory_15
    challenges_subcategoryproficiencyaward_71.proficiency = challenges_proficiency_1
    challenges_subcategoryproficiencyaward_71.xp_reward = 112
    challenges_subcategoryproficiencyaward_71 = importer.save_or_locate(challenges_subcategoryproficiencyaward_71)

    challenges_subcategoryproficiencyaward_72 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_72.subcategory = challenges_subcategory_15
    challenges_subcategoryproficiencyaward_72.proficiency = challenges_proficiency_2
    challenges_subcategoryproficiencyaward_72.xp_reward = 1001
    challenges_subcategoryproficiencyaward_72 = importer.save_or_locate(challenges_subcategoryproficiencyaward_72)

    challenges_subcategoryproficiencyaward_73 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_73.subcategory = challenges_subcategory_15
    challenges_subcategoryproficiencyaward_73.proficiency = challenges_proficiency_3
    challenges_subcategoryproficiencyaward_73.xp_reward = 2001
    challenges_subcategoryproficiencyaward_73 = importer.save_or_locate(challenges_subcategoryproficiencyaward_73)

    challenges_subcategoryproficiencyaward_74 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_74.subcategory = challenges_subcategory_15
    challenges_subcategoryproficiencyaward_74.proficiency = challenges_proficiency_4
    challenges_subcategoryproficiencyaward_74.xp_reward = 3001
    challenges_subcategoryproficiencyaward_74 = importer.save_or_locate(challenges_subcategoryproficiencyaward_74)

    challenges_subcategoryproficiencyaward_75 = SubcategoryProficiencyAward()
    challenges_subcategoryproficiencyaward_75.subcategory = challenges_subcategory_15
    challenges_subcategoryproficiencyaward_75.proficiency = challenges_proficiency_5
    challenges_subcategoryproficiencyaward_75.xp_reward = 4001
    challenges_subcategoryproficiencyaward_75 = importer.save_or_locate(challenges_subcategoryproficiencyaward_75)

    # Processing model: challenges.models.Challenge

    from challenges.models import Challenge

    challenges_challenge_1 = Challenge()
    challenges_challenge_1.name = 'Say Hello World!'
    challenges_challenge_1.description = challenges_challengedescription_1
    challenges_challenge_1.difficulty = 0.0
    challenges_challenge_1.score = 10
    challenges_challenge_1.test_file_name = 'hello_tests'
    challenges_challenge_1.test_case_count = 1
    challenges_challenge_1.category = challenges_subcategory_15
    challenges_challenge_1 = importer.save_or_locate(challenges_challenge_1)

    challenges_challenge_1.supported_languages.add(challenges_language_1)
    challenges_challenge_1.supported_languages.add(challenges_language_2)
    challenges_challenge_1.supported_languages.add(challenges_language_3)
    challenges_challenge_1.supported_languages.add(challenges_language_4)
    challenges_challenge_1.supported_languages.add(challenges_language_5)
    challenges_challenge_1.supported_languages.add(challenges_language_6)

    challenges_challenge_2 = Challenge()
    challenges_challenge_2.name = 'Basic Numbers'
    challenges_challenge_2.description = challenges_challengedescription_2
    challenges_challenge_2.difficulty = 4.5
    challenges_challenge_2.score = 40
    challenges_challenge_2.test_file_name = 'basic_numbers_tests'
    challenges_challenge_2.test_case_count = 8
    challenges_challenge_2.category = challenges_subcategory_14
    challenges_challenge_2 = importer.save_or_locate(challenges_challenge_2)

    challenges_challenge_2.supported_languages.add(challenges_language_1)
    challenges_challenge_2.supported_languages.add(challenges_language_2)
    challenges_challenge_2.supported_languages.add(challenges_language_3)
    challenges_challenge_2.supported_languages.add(challenges_language_4)
    challenges_challenge_2.supported_languages.add(challenges_language_5)
    challenges_challenge_2.supported_languages.add(challenges_language_6)

    challenges_challenge_3 = Challenge()
    challenges_challenge_3.name = 'Array Sum'
    challenges_challenge_3.description = challenges_challengedescription_3
    challenges_challenge_3.difficulty = 1.0
    challenges_challenge_3.score = 10
    challenges_challenge_3.test_file_name = 'array_sum_tests'
    challenges_challenge_3.test_case_count = 7
    challenges_challenge_3.category = challenges_subcategory_15
    challenges_challenge_3 = importer.save_or_locate(challenges_challenge_3)

    challenges_challenge_3.supported_languages.add(challenges_language_1)
    challenges_challenge_3.supported_languages.add(challenges_language_2)
    challenges_challenge_3.supported_languages.add(challenges_language_3)
    challenges_challenge_3.supported_languages.add(challenges_language_4)
    challenges_challenge_3.supported_languages.add(challenges_language_5)
    challenges_challenge_3.supported_languages.add(challenges_language_6)

    challenges_challenge_4 = Challenge()
    challenges_challenge_4.name = 'Array Amplitude'
    challenges_challenge_4.description = challenges_challengedescription_4
    challenges_challenge_4.difficulty = 1.0
    challenges_challenge_4.score = 10
    challenges_challenge_4.test_file_name = 'array_amplitude_tests'
    challenges_challenge_4.test_case_count = 10
    challenges_challenge_4.category = challenges_subcategory_15
    challenges_challenge_4 = importer.save_or_locate(challenges_challenge_4)

    challenges_challenge_4.supported_languages.add(challenges_language_1)
    challenges_challenge_4.supported_languages.add(challenges_language_2)
    challenges_challenge_4.supported_languages.add(challenges_language_3)
    challenges_challenge_4.supported_languages.add(challenges_language_4)
    challenges_challenge_4.supported_languages.add(challenges_language_5)
    challenges_challenge_4.supported_languages.add(challenges_language_6)

    challenges_challenge_5 = Challenge()
    challenges_challenge_5.name = 'Lava World'
    challenges_challenge_5.description = challenges_challengedescription_5
    challenges_challenge_5.difficulty = 3.5
    challenges_challenge_5.score = 30
    challenges_challenge_5.test_file_name = 'lava_world_tests'
    challenges_challenge_5.test_case_count = 6
    challenges_challenge_5.category = challenges_subcategory_13
    challenges_challenge_5 = importer.save_or_locate(challenges_challenge_5)

    challenges_challenge_5.supported_languages.add(challenges_language_1)
    challenges_challenge_5.supported_languages.add(challenges_language_2)
    challenges_challenge_5.supported_languages.add(challenges_language_3)
    challenges_challenge_5.supported_languages.add(challenges_language_4)
    challenges_challenge_5.supported_languages.add(challenges_language_5)
    challenges_challenge_5.supported_languages.add(challenges_language_6)

    challenges_challenge_6 = Challenge()
    challenges_challenge_6.name = 'Labyrinth Adventure'
    challenges_challenge_6.description = challenges_challengedescription_6
    challenges_challenge_6.difficulty = 4.5
    challenges_challenge_6.score = 40
    challenges_challenge_6.test_file_name = 'labyrinth_adventure_tests'
    challenges_challenge_6.test_case_count = 9
    challenges_challenge_6.category = challenges_subcategory_14
    challenges_challenge_6 = importer.save_or_locate(challenges_challenge_6)

    challenges_challenge_6.supported_languages.add(challenges_language_1)
    challenges_challenge_6.supported_languages.add(challenges_language_2)
    challenges_challenge_6.supported_languages.add(challenges_language_3)
    challenges_challenge_6.supported_languages.add(challenges_language_4)
    challenges_challenge_6.supported_languages.add(challenges_language_5)
    challenges_challenge_6.supported_languages.add(challenges_language_6)

    challenges_challenge_7 = Challenge()
    challenges_challenge_7.name = 'Lawnmower'
    challenges_challenge_7.description = challenges_challengedescription_7
    challenges_challenge_7.difficulty = 4.5
    challenges_challenge_7.score = 35
    challenges_challenge_7.test_file_name = 'lawnmower_tests'
    challenges_challenge_7.test_case_count = 9
    challenges_challenge_7.category = challenges_subcategory_14
    challenges_challenge_7 = importer.save_or_locate(challenges_challenge_7)

    challenges_challenge_7.supported_languages.add(challenges_language_1)
    challenges_challenge_7.supported_languages.add(challenges_language_2)
    challenges_challenge_7.supported_languages.add(challenges_language_3)
    challenges_challenge_7.supported_languages.add(challenges_language_4)
    challenges_challenge_7.supported_languages.add(challenges_language_5)
    challenges_challenge_7.supported_languages.add(challenges_language_6)

    challenges_challenge_8 = Challenge()
    challenges_challenge_8.name = "Rodger's Rise"
    challenges_challenge_8.description = challenges_challengedescription_8
    challenges_challenge_8.difficulty = 3.0
    challenges_challenge_8.score = 20
    challenges_challenge_8.test_file_name = 'rodger_rise_tests'
    challenges_challenge_8.test_case_count = 10
    challenges_challenge_8.category = challenges_subcategory_11
    challenges_challenge_8 = importer.save_or_locate(challenges_challenge_8)

    challenges_challenge_8.supported_languages.add(challenges_language_1)
    challenges_challenge_8.supported_languages.add(challenges_language_2)
    challenges_challenge_8.supported_languages.add(challenges_language_3)
    challenges_challenge_8.supported_languages.add(challenges_language_4)
    challenges_challenge_8.supported_languages.add(challenges_language_5)
    challenges_challenge_8.supported_languages.add(challenges_language_6)

    challenges_challenge_9 = Challenge()
    challenges_challenge_9.name = 'Factory Factorization'
    challenges_challenge_9.description = challenges_challengedescription_9
    challenges_challenge_9.difficulty = 3.5
    challenges_challenge_9.score = 24
    challenges_challenge_9.test_file_name = 'factory_factorization_tests'
    challenges_challenge_9.test_case_count = 17
    challenges_challenge_9.category = challenges_subcategory_11
    challenges_challenge_9 = importer.save_or_locate(challenges_challenge_9)

    challenges_challenge_9.supported_languages.add(challenges_language_1)
    challenges_challenge_9.supported_languages.add(challenges_language_2)
    challenges_challenge_9.supported_languages.add(challenges_language_3)
    challenges_challenge_9.supported_languages.add(challenges_language_4)
    challenges_challenge_9.supported_languages.add(challenges_language_5)
    challenges_challenge_9.supported_languages.add(challenges_language_6)

    challenges_challenge_10 = Challenge()
    challenges_challenge_10.name = 'Toys for the Boys'
    challenges_challenge_10.description = challenges_challengedescription_10
    challenges_challenge_10.difficulty = 4.5
    challenges_challenge_10.score = 35
    challenges_challenge_10.test_file_name = 'toys_for_the_boys_tests'
    challenges_challenge_10.test_case_count = 11
    challenges_challenge_10.category = challenges_subcategory_9
    challenges_challenge_10 = importer.save_or_locate(challenges_challenge_10)

    challenges_challenge_10.supported_languages.add(challenges_language_1)
    challenges_challenge_10.supported_languages.add(challenges_language_2)
    challenges_challenge_10.supported_languages.add(challenges_language_3)
    challenges_challenge_10.supported_languages.add(challenges_language_4)
    challenges_challenge_10.supported_languages.add(challenges_language_5)
    challenges_challenge_10.supported_languages.add(challenges_language_6)

    # Processing model: challenges.models.Submission

    from challenges.models import Submission


    # Processing model: challenges.models.SubmissionVote

    from challenges.models import SubmissionVote


    # Processing model: challenges.models.TestCase

    from challenges.models import TestCase


