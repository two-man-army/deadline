# Currently only works with INTEGER numbers

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
  def initialize(value = NIL, min = NIL, max = NIL)
    @name = NIL
    @value = value
    @min = min
    @max = max
  end

  def value
    @value
  end

  def value=(val)
    @value = val
  end

  def gen_value(rnd_obj)
    @value = rnd_obj.rand(@min..@max)
  end
end


# Holds a variable that depends on other values
class DependantVariable < Variable
  def initialize(name = NIL, value = NIL, min = NIL, max = NIL)
    @name = name
    @value = value  # should be a Variable instance
    @min = min
    @max = max
  end

  def value
    if @value.nil?
      raise Exception("#{@name}'s value is not generated!")
    end
    @value
  end

  def gen_value(rnd_obj)
    min_value = @min
    max_value = @max
    if @min.is_a? Variable
      min_value = @min.value
    end
    if @max.is_a? Variable
      max_value = @max.value
    end
    @value = rnd_obj.rand(min_value..max_value)
  end
end


class Generator
  def initialize(input_content)
    @input_content = input_content
    @rnd_obj = Random.new
  end

  # @return [String]
  def generate
    output_string = ''

    unless @input_content.initialization_part.nil?
      output_string += generate_output @input_content.initialization_part
    end
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
    (0...repeat_count).each{||
      input_format.structure.each{|struct|
        curr_output += [parse_structure(struct), "\n"]
      }

      output << curr_output.join
    }

    output.join "\n"
  end

  # given a list of variables (or lists of lists), convert them to a string
  def parse_structure(struct)
    if struct.class.method_defined? :map
      str = struct.map{|var| parse_structure var}
      str.join ' '
    elsif struct.class.method_defined? :get_structure
      parse_structure struct.get_structure
    else
      struct.gen_value(@rnd_obj)
    end
  end

end

# Contains a part of the input, i.e the initialization phase
class InputFormat
  attr_reader :repeat_count, :name, :structure
  def initialize(repeat_count, structure, name)
    @name = name
    @repeat_count = repeat_count
    @structure = structure  # a list of lists of Variable objects
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
    puts 'Currently building: INITIALIZATION PHASE'
    puts 'Enter the number of initialization lines'
    init_line_count = gets.chomp.to_i
    initialization_structure = []  # list of lists of variables
    (1..init_line_count).each {|line|
      puts "At line #{line}"
      puts 'Enter the name of the variables, separated by space'
      variables = gets.chomp.split
      populated_vars = variables.map {|varname|
        var = parse_variable varname
        @variables[varname] = var
        var
      }  # populate the variables
      initialization_structure << populated_vars
    }
    puts "INIT STRUCTURE #{initialization_structure}"
    InputFormat.new(1, initialization_structure, 'hope i die')
  end

  def parse_content
    puts 'Currently building: CONTENT PHASE'
    puts 'Enter the number of content pairs (overall line count)'
    content_structure = []
    content_line_count, _ = parse_variable_value

    pair = parse_pair
    (0...content_line_count).each {||
      content_structure << pair
    }

    puts "CONTENT STRUCTURE #{content_structure}"
    InputFormat.new(1, content_structure, 'hope i die')
  end

  # parses a pair of content
  def parse_pair
    puts 'Currently building a content pair'
    puts 'Enter the number of lines each pair requires'
    line_count = gets.chomp.to_i
    pair_structure = []
    # TODO: add option to parse variables again
    (0...line_count).each {|ln|
      puts "At line #{ln} of pair, enter number count"
      element_count, _ = parse_variable_value
      element = parse_variable "array element"
      pair_structure << InputStructure.new(element_count, element)
    }

    pair_structure
  end

  def parse_variable(varname)
    is_dependant = false  # tracks if the variable is dependant on other vars
    puts "Building variable #{varname.upcase}"
    puts 'Enter lower limit of the variable (variable name or number)'
    lower, was_dep = parse_variable_value
    is_dependant |= was_dep
    puts 'Enter upper limit of the variable (variable name or number)'
    upper, was_dep = parse_variable_value
    is_dependant |= was_dep

    if is_dependant
      var = DependantVariable.new(name=varname, value=NIL, min=lower, max=upper)
      # var.gen_value @rnd_obj
      @variables[varname] = var
      var
    else
      var = IndependantVariable.new(value=NIL, min=lower, max=upper)
      # var.gen_value @rnd_obj
      var
    end
  end

  # parses a variable, either by converting it to an integer or fetching its Variable object's value
  # @return [Fixnum, Boolean] - the number and a boolean indicating if it was a variable
  def parse_variable_value
    variable = gets.chomp
    if variable.is_number?
      return variable.to_i, false
    else
      unless @variables.key?(variable)
        raise Exception("Variable #{variable} does not exist!")
      end
      return @variables[variable]
    end
  end
end


class InputStructure
  def initialize(line_count, element)
    @line_count = line_count
    @element = element
  end

  def get_structure
    line_count = @line_count
    if line_count.is_a? Variable
      if line_count.value.nil?
        line_count.gen_value
      end
      line_count = line_count.value

      (0...line_count).map{@element.clone}
    end
  end
end

require_relative 'test_case_validator.rb'
def main
  ip = InputParser.new
  input_content = ip.parse_input
  (0..5).each {|idx|
    gen = Generator.new(input_content)
    input = gen.generate
    ts_val = NaiveTestCaseValidator.new(input, "test.py", 5, true)
    ts_val.run_program
    if ts_val.validate
      File.open("tank_input#{idx}.txt", 'w').write(input)
      File.open("tank_output#{idx}.txt", 'w').write(ts_val.program_output)
    else
      redo
    end
  }

end
# create a sample input
# one N - count of array
# N elements array
main