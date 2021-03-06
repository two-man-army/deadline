# Currently only works with INTEGER numbers
require_relative 'variables.rb'
require 'set'

# Reads input from the user
class Object
  def is_number?
    self.to_f.to_s == self.to_s || self.to_i.to_s == self.to_s
  end
end

# Given an InputContent object, goes through all the input and generates it
#  dynamically
class InputGenerator
  def initialize(input_content, generate_harder=false, allow_duplicates=false)
    @input_content = input_content
    @rnd_obj = Random.new
    @generate_harder = generate_harder
    @no_duplicates = !allow_duplicates
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
    # TODO: InputFormat should not have repeat count
    (0...repeat_count).each do
      if_struct = input_format.content

      if_struct.each do |struct|
        @duplicates = Set.new  # reset duplicates for each new line
        puts "STRUCT IS #{struct}"
        curr_output += [parse_structure(struct), "\n"]
      end

      output << curr_output.join
    end

    output.join "\n"
  end


  def parse_structure(struct)
    # We're given a Structure, so spread it and parse its content
    inner_struct_parse struct.spread_structure
  end

  # given a list of variables (or lists of lists, or Structure objects), convert them to a string
  # as Structures can be deeply nested, we need some recursion here
  def inner_struct_parse(s)
    if s.class.method_defined? :map
      # We're down to a list, so call parse on every element in it
      str = s.each_with_index.map do |var, idx|
        inner_struct_parse var
        # TODO: decide how to impose limits e.g 30% factors
      end
      str.join ' '
    elsif s.class.method_defined? :spread_structure
      # We're down to a Structure, so spread it
      inner_struct_parse s.spread_structure
    else
      # We're down to a variable, generate it
      generate_variable_value s
      s.value
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
  attr_reader :repeat_count, :name, :content
  def initialize(repeat_count, content, name)
    @name = name
    @repeat_count = repeat_count
    @content = content # a list of InputStructure objects
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

# Holds a structured input, maybe dependant on variables
class InputStructure
  def initialize(line_count, element)
    @line_count = line_count
    @element = element
  end

  # spreads the structure if the line_count is a Variable
  def spread_structure
    # return unless @line_count.is_a? Variable
    line_count = @line_count
    if @line_count.is_a? Variable
      line_count = @line_count
      line_count.gen_value if line_count.value.nil?
      line_count = line_count.value
    end
    (0...line_count).map{ @element.clone } # clone the element
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
      initialization_structure << InputStructure.new(1, populated_vars)
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
    content_structure = InputStructure.new(content_line_count, pair)
    puts "CONTENT STRUCTURE #{content_structure}"
    InputFormat.new(1, [content_structure], 'Content Phase')
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
      puts 'Do you want to have the same variable repeated? (y\n)'
      if gets.chomp == 'y'
        element = parse_variable 'array element'
        puts 'Do you want your array element to have a depend on another variable? (y\n)'
        if gets.chomp == 'y'
          puts 'Pick a number or variable that you want your array element to be a factor of'
          factor, = parse_variable_value
          element.factor_of = factor
          puts 'Rougly what percentage of the numbers do you want to be factors? 1-100'
          percentage = gets.chomp
          if not percentage.is_number? or percentage.to_i < 0 or percentage.to_i > 100
            raise Exception('INVALID PERCENTAGE')
          end
          element.factor_percentage = percentage.to_i
        end
        pair_structure << InputStructure.new(element_count, element)
      else
        puts 'Enter the name of the variables, separated by space'
        variables = gets.chomp.split
        populated_vars = populate_variables variables
        pair_structure << populated_vars
      end
    end

    pair_structure
  end

  def parse_variable(varname)
    is_dependant = false # tracks if the variable is dependant on other vars
    puts "Building variable #{varname.upcase}"
    puts 'Enter upper limit of the variable (variable name or number, or expression containing variable surrounded by space - e.g Math.sqrt( n )'
    lower, was_dep = parse_variable_value
    puts 'Enter upper limit of the variable (variable name or number, or expression containing variable surrounded by space - e.g Math.sqrt( n )'
    # TODO: Add expression. i.e N-1
    upper, was_dep2 = parse_variable_value
    is_dependant |= was_dep | was_dep2

    variable = create_variable(lower, upper, varname, is_dependant)
    @variables[varname] = variable if is_dependant
    variable
  end

  def create_variable(lower, upper, name, is_dependant)
    if is_dependant
      DependantVariable.new(name, NIL, lower, upper, NIL)
    else
      IndependantVariable.new(name, NIL, lower, upper, NIL)
    end
  end

  # parses a variable, either by converting it to an integer
  #   or fetching its Variable object's value
  # @return [Fixnum, Boolean] - the number and a boolean
  #   indicating if it was a variable
  def parse_variable_value
    variable = gets.chomp
    return variable.to_i, false if variable.is_number?

    is_an_expression = variable.split(' ').length > 1
    if is_an_expression
      # find the variable
      exp_var = NIL
      variable.split(' ').each do |v|
        if @variables.key?(v)
          if !exp_var.nil? && exp_var != @variables[v]
            raise Exception('Cannot have two different variables in the expression!')
          end
          exp_var = @variables[v]
        end
      end

      return VariableExpression.new(exp_var, variable), true
    end

    unless @variables.key?(variable)
      puts @variables
      @variables.key?(variable)
      raise Exception.new("Variable #{variable} does not exist!")
    end
    return @variables[variable], true
  end
end
