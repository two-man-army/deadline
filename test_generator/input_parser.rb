# Currently only works with INTEGER numbers
require_relative 'test_case_validator.rb'
require 'set'

# Reads input from the user
class Object
  def is_number?
    self.to_f.to_s == self.to_s || self.to_i.to_s == self.to_s
  end
end


class Variable
end


# Holds a constant variable which depends on constant values
class IndependantVariable < Variable
  attr_accessor :value
  def initialize(value = NIL, min = NIL, max = NIL)
    @name = NIL
    @value = value
    @min = min
    @max = max
  end

  def gen_value(rnd_obj)
    @value = rnd_obj.rand(@min..@max)
  end

  # Generates a higher value
  def gen_harder_value(rnd_obj)
    # generate from the top 70% upwards
    diff = @max-@min
    top_seventy_percent = 0.7 * diff
    @value = rnd_obj.rand(Integer(top_seventy_percent)..@max)
  end
end


# Holds a variable that depends on other values
class DependantVariable < Variable
  def initialize(name = NIL, value = NIL, min = NIL, max = NIL)
    @name = name
    @value = value # should be a Variable instance
    @min = min
    @max = max
  end

  def value
    raise Exception("#{@name}'s value is not generated!") if @value.nil?

    @value
  end

  def gen_value(rnd_obj)
    min_value = @min
    max_value = @max

    min_value = @min.value if @min.is_a? Variable
    max_value = @max.value if @max.is_a? Variable

    @value = rnd_obj.rand(min_value..max_value)
  end
end


# Given an InputContent object, goes through all the input and generates it
#  dynamically
class Generator
  def initialize(input_content, generate_harder=false)
    @input_content = input_content
    @rnd_obj = Random.new
    @generate_harder = generate_harder
    @no_duplicates = true
    @duplicates = Set.new
  end

  # @return [String]
  def generate
    output_string = ''

    unless @input_content.initialization_part.nil?
      output_string += generate_output @input_content.initialization_part
    end
    @generate_harder = false  # only generate higher values for the initialization
    unless @input_content.content_part.nil?
      output_string += generate_output @input_content.content_part
    end
    unless @input_content.annexation.nil?
      output_string += generate_output @input_content.annexation
    end

    output_string
  end

  # generates input from the given input format
  def generate_output(input_format)
    puts input_format
    repeat_count = input_format.repeat_count
    repeat_count = repeat_count.value if repeat_count.is_a? Variable
    output = []
    curr_output = []
    (0...repeat_count).each do
      input_format.structure.each do |struct|
        curr_output += [parse_structure(struct), "\n"]
      end

      output << curr_output.join
    end

    output.join "\n"
  end

  # given a list of variables (or lists of lists), convert them to a string
  def parse_structure(struct)
    if struct.class.method_defined? :map
      str = struct.map { |var| parse_structure var }
      str.join ' '
    elsif struct.class.method_defined? :spread_structure
      parse_structure struct.spread_structure
    else
      generate_variable_value struct
      struct.value
    end
  end

  # given a variable, generate a value for it and add it to the duplicates
  def generate_variable_value(variable)
    loop do
      generated_value = if @generate_harder
                          variable.gen_harder_value(@rnd_obj)
                        else
                          variable.gen_value(@rnd_obj)
                        end
      break unless handle_dup_value_generation generated_value
    end
  end

  # handles a duplicate value generation if @no_duplicates flag is set
  # @return [Bool] - if the value is a duplicate
  def handle_dup_value_generation(value)
    return false unless @no_duplicates

    if @duplicates.include? value
      puts "#{value} is a duplicate, redoing"
      true
    else
      @duplicates.add value
      false
    end
  end
end

# Contains a part of the input, i.e the initialization phase
class InputFormat
  attr_reader :repeat_count, :name, :structure
  def initialize(repeat_count, structure, name)
    @name = name
    @repeat_count = repeat_count
    @structure = structure # a list of lists of Variable objects
  end
end

# Contains numerous InputFormats, constituting the whole input
class InputContent
  attr_reader :initialization_part, :content_part, :annexation

  def initialize(setup_part, content_part, annexation)
    @initialization_part = setup_part
    @content_part = content_part
    @annexation = annexation
  end
end

# Parses input variables into Variable objects
class InputParser
  def initialize
    @variables = {}
    @rnd_obj = Random.new
  end

  def parse_input
    init_struct = parse_initialization
    content_struct = parse_content
    # TODO: parse_annexation

    InputContent.new(init_struct, content_struct, NIL)
  end

  def parse_initialization
    puts "Currently building: INITIALIZATION PHASE\n" \
         'Enter the number of initialization lines'
    init_line_count = gets.chomp.to_i
    initialization_structure = [] # list of lists of variables
    (1..init_line_count).each do |line|
      puts "At line #{line}\nEnter the name of the variables, separated by space"
      variables = gets.chomp.split
      populated_vars = populate_variables variables
      initialization_structure << populated_vars
    end
    puts "INIT STRUCTURE #{initialization_structure}"
    InputFormat.new(1, initialization_structure, 'Initialization Phase')
  end

  # Given a list of variables, parse them and populate the @variables list
  def populate_variables(variables)
    variables.map do |var_name|
      var = parse_variable var_name
      @variables[var_name] = var
      var
    end
  end

  def parse_content
    puts 'Currently building: CONTENT PHASE'
    puts 'Enter the number of content pairs (overall line count)'
    content_structure = []
    content_line_count, = parse_variable_value

    pair = parse_pair
    (0...content_line_count).each do ||
      content_structure << pair
    end

    puts "CONTENT STRUCTURE #{content_structure}"
    InputFormat.new(1, content_structure, 'hope i die')
  end

  # parses a pair of content
  def parse_pair
    puts "Currently building a content pair\n"\
         'Enter the number of lines each pair requires'
    line_count = gets.chomp.to_i
    pair_structure = []
    # TODO: add option to parse variables again
    (0...line_count).each do |ln|
      puts "At line #{ln} of pair, enter number count"
      element_count, = parse_variable_value
      element = parse_variable 'array element'
      pair_structure << InputStructure.new(element_count, element)
    end

    pair_structure
  end

  def parse_variable(varname)
    is_dependant = false # tracks if the variable is dependant on other vars
    puts "Building variable #{varname.upcase}"
    puts 'Enter lower limit of the variable (variable name or number)'
    lower, was_dep = parse_variable_value
    puts 'Enter upper limit of the variable (variable name or number)'
    upper, was_dep2 = parse_variable_value
    is_dependant |= was_dep | was_dep2

    variable = create_variable(lower, upper, varname, is_dependant)
    @variables[varname] = variable if is_dependant
    variable
  end

  def create_variable(lower, upper, name, is_dependant)
    if is_dependant
      DependantVariable.new(name, NIL, lower, upper)
    else
      IndependantVariable.new(NIL, lower, upper)
    end
  end

  # parses a variable, either by converting it to an integer
  #   or fetching its Variable object's value
  # @return [Fixnum, Boolean] - the number and a boolean
  #   indicating if it was a variable
  def parse_variable_value
    variable = gets.chomp
    return variable.to_i, false if variable.is_number?

    unless @variables.key?(variable)
      raise Exception("Variable #{variable} does not exist!")
    end
    @variables[variable]
  end
end

# Holds a structured input, maybe dependant on variables
class InputStructure
  def initialize(line_count, element)
    @line_count = line_count
    @element = element
  end

  # spreads the structure if the line_count is a Variable
  def spread_structure
    return unless @line_count.is_a? Variable

    line_count = @line_count
    line_count.gen_value if line_count.value.nil?
    line_count = line_count.value

    (0...line_count).map{ @element.clone } # clone the element
  end
end

# Generated the naive test cases for a program
class NaiveTestCaseGenerator
  def initialize(test_count, timeout_seconds, input_content, naive_file_name)
    @test_count = test_count
    @input_content = input_content
    @timeout_seconds = timeout_seconds
    @naive_file_name = naive_file_name
    @test_case_idx = 0
  end

  def generate_naive_test_cases(test_count)
    (0...Integer(test_count)).each do
      gen = Generator.new(@input_content)
      input = gen.generate
      ts_val = NaiveTestCaseValidator.new(input, @naive_file_name,
                                          @timeout_seconds, true)
      ts_val.run_program
      is_valid = ts_val.validate
      puts "PROGRAM VALID? #{is_valid} #{input[1, 20]}"
      redo unless is_valid
      File.open("input_#{@test_case_idx+1}.txt", 'w').write(input)
      File.open("output_#{@test_case_idx+1}.txt", 'w').write(ts_val.program_output)
      @test_case_idx += 1
    end
  end

  def generate
    puts "Generating Naive Only #{@test_count} tests."
    generate_naive_test_cases(@test_count)
  end
end

# Generate a certain amount of naive and good test cases
class GoodAndNaiveTestCaseGenerator < NaiveTestCaseGenerator
  # @param [Integer] naive_percentage - 1-100 integer,
  #             denoting how much percentage of test cases
  #             we want to be passable by the naive tests
  def initialize(test_case_count, timeout_seconds, input_content, naive_file_name, good_file_name, naive_percentage)
    @good_file_name = good_file_name
    @naive_percentage = naive_percentage
    @naive_test_case_count = Integer((naive_percentage/100.0) * test_case_count)
    @good_test_case_count = Integer((1-(naive_percentage/100.0)) * test_case_count)
    super(@naive_test_case_count, timeout_seconds, input_content, naive_file_name)
  end

  def generate_good_test_cases(test_count)
    gen_harder = false
    (0...test_count).each do
      gen = Generator.new(@input_content, gen_harder)
      input = gen.generate
      ts_val = NaiveTestCaseValidator.new(input, @good_file_name, 5, true)
      ts_val.run_program
      good_results = ts_val.validate
      naive_val = NaiveTestCaseValidator.new(input, @naive_file_name, 5, false)
      naive_val.run_program
      naive_results = naive_val.validate
      puts "naive #{naive_results} and good #{good_results}"
      # assert that the good test has passed and the naived not
      unless good_results && naive_results
        puts 'generating harder'
        gen_harder = true
        redo
      end

      File.open("input_#{@test_case_idx+1}.txt", 'w').write(input)
      File.open("output_#{@test_case_idx+1}.txt", 'w').write(ts_val.program_output)
      @test_case_idx+=1
      gen_harder = false
    end
  end

  def generate
    puts "Generating #{@naive_test_case_count} naive tests"
    generate_naive_test_cases(@naive_test_case_count)
    puts "Generating #{@good_test_case_count} non-naive tests "
    generate_good_test_cases(@good_test_case_count)
  end
end


def main
  ip = InputParser.new
  input_content = ip.parse_input
  puts 'Do you have two solutions (good solution and naive)? (y/n)'
  test_case_count = 10
  ans = gets.chomp

  if ans.include? 'y'
    puts 'How many (in percentage) test cases do you want to pass with the naive solution?'
    percentage = gets.chomp
    if not percentage.is_number? or percentage.to_i < 0 or percentage.to_i > 100
      raise Exception('INVALID PERCENTAGE')
    end
    test_gen = GoodAndNaiveTestCaseGenerator.new(
      test_case_count, 5, input_content, 'min_diff_naive.py',
      'min_diff_good.py', percentage.to_i)
  else
    test_gen = NaiveTestCaseGenerator.new(5, 5, input_content, 'min_diff_naive.py')
  end
  test_gen.generate
end
# create a sample input
# one N - count of array
# N elements array
main