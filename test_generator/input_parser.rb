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
    puts @min
    puts @max
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
# TODO: STRUCT CLASSES


  # generates input from the given input format
  def generate_output(input_format)
    puts input_format
    repeat_count = input_format.repeat_count
    if repeat_count.is_a? Variable
      repeat_count = repeat_count.value
    end
    output = []
    curr_output = []
    (0...repeat_count).each{||
      puts "INPUT FORMAT #{input_format}"
      puts "INPUT STRUCTURE #{input_format.structure}"
      input_format.structure.each{|struct|
        # convert list of variables to a string
        output = struct.map {|inner_struct|
          puts "INNER STRUCT #{inner_struct}"
          if inner_struct.class.method_defined? :map
            str = inner_struct.map{|var|
              var.gen_value(@rnd_obj)
            }
            str.join ' '
          else
            inner_struct
          end
        }
        puts "OUTPUT IS #{output}"
        curr_output << output.join(' ')
        curr_output << "\n"
      }

      output << curr_output.join
    }
    puts "output #{output}"

    output.join "\n"
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

    return InputContent.new(init_struct, content_struct, NIL)
    # parse_annexation
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
    content_structuer = []
    content_line_count = parse_variable_value

    pair = parse_pair
    (0...content_line_count).each {||
      content_structuer << pair
    }

    puts "CONTENT STRUCTURE #{content_structuer}"
    InputFormat.new(1, content_structuer, 'hope i die')
  end

  # parses a pair of content
  def parse_pair
    puts 'Currently building a content pair'
    puts 'Enter the number of lines each pair requires'
    line_count = parse_variable_value
    pair_structure = []
    # TODO: add option to parse variables again
    (0...line_count).each {|ln|
      puts 'At line #{ln} of pair, enter number count'
      element_count = parse_variable_value
      element = parse_variable "array element"
      pair_structure << (0...element_count).map{element.clone}
    }

    pair_structure
  end

  def parse_variable(varname)
    is_dependant = false  # tracks if the variable is dependant on other vars
    puts "Building variable #{varname.upcase}"
    puts 'Enter lower limit of the variable (variable name or number)'
    lower = gets.chomp
    unless lower.is_number?
      # lower is a variable
      unless @variables.key?(lower)
        raise Exception("Variables #{lower} was not defined!")
      end
      lower = @variables[lower]
      is_dependant = true
    else
      lower = lower.to_i
    end
    puts 'Enter upper limit of the variable (variable name or number)'
    upper = gets.chomp
    unless upper.is_number?
      # upper is a variable
      unless @variables.key?(upper)
        raise Exception("Variables #{upper} was not defined!")
      end
      upper = @variables[upper]
      is_dependant = true
    else
      upper = upper.to_i
    end


    if is_dependant
      var = DependantVariable.new(name=varname, value=NIL, min=lower, max=upper)
      var.gen_value @rnd_obj
      @variables[varname] = var
      var
    else
      var = IndependantVariable.new(value=NIL, min=lower, max=upper)
      var.gen_value @rnd_obj
      var
    end
  end

  # parses a variable, either by converting it to an integer or fetching its Variable object's value
  def parse_variable_value
    variable = gets.chomp
    if variable.is_number?
      return variable.to_i
    else
      unless @variables.key?(variable)
        raise Exception("Variable #{variable} does not exist!")
      end
      return @variables[variable].value
    end
  end
end
# create a sample input
# one N - count of array
# N elements array
ip = InputParser.new
input_content = ip.parse_input
gen = Generator.new(input_content)
gen.generate











#
#
#
# puts 'Enter the total amount of test cases you want'
# test_case_count = gets.chomp.to_i
#
# puts 'Currently building: SETUP FORM. This is where you set up various variables to' +
#      'later reference and impose limits with.'
#
# puts 'Enter the number of input lines'
# input_line_count = gets.to_i
# variable_limits = {}
# variable_structure = []  # hold the order of the variables to come
# (1..input_line_count).each {|line|
#   puts "Line #{line}, enter the name of the variables, separated by space"
#   variables = gets.split
#   puts "Your variables are: #{variables}"
#   variable_structure << variables
#   variables.each {|var|
#     # TODO: add upper/lower limit be another variable
#     puts "Enter the lower limit for variable #{var.upcase}"
#     lower_limit = gets.to_i
#     puts "Enter the upper limit for variable #{var.upcase}"
#     upper_limit = gets.to_i
#
#     variable_limits[var] = [lower_limit, upper_limit]  # TODO: Maybe convert var to a class?
#   }
# }
#
# puts 'Currently building: CONTENT FORM. This is the meat of the input'
# puts 'Enter the number of lines that will constitute a single pair of input line (can be another variable)'
# pair_lines_count = gets.chomp
# puts pair_lines_count.is_number?
# if pair_lines_count.is_number?
#   pair_lines_count = pair_lines_count.to_i
# end
# puts 'Enter the number of overall lines you will have (can be another variable)'
# line_count = gets.chomp
# if line_count.is_number?
#   line_count = line_count.to_i
# end
#
# # build each pair's limits
# pair_structure = []
# (1..pair_lines_count).each {|pair|
#   # build an array
#   puts "Pair line #{pair}, enter the number of the variables"
#   var_count = gets.chomp
#   if var_count.is_number?
#     var_count = var_count.to_i
#   end
#   puts "Enter lower limit for each number"
#   low_limit = gets.chomp
#   if low_limit.is_number?
#     low_limit = low_limit.to_i
#   end
#   puts "Enter upper limit for each number"
#   upp_limit = gets.chomp
#   if upp_limit.is_number?
#     upp_limit = upp_limit.to_i
#   end
#   pair_structure << [var_count, low_limit, upp_limit]
# }
#
# # TODO: get annexation part
#
# rnd = Random.new
#
# (0...test_case_count).each {|test|
#   File.open("input_#{test}.txt", 'w') { |file|
#     # start building output
#     # INPUT PART
#     variable_values = {}
#     variable_structure.each{|line|
#       output = []
#       line.each{|var|
#         # assign a value to the variable
#         low, max = variable_limits[var]
#         # some other variables are the limit
#         unless low.is_number?
#           low = variable_values[low]
#         end
#         unless max.is_number?
#           max = variable_values[max]
#         end
#         variable_values[var] = rnd.rand(low..max)
#         output << variable_values[var]
#       }
#       input_part = output.join(' ')
#       puts input_part
#       file.puts input_part
#     }
#
#     # CONTENT PART
#     unless line_count.is_number?
#       line_count = variable_values[var]
#     end
#     # build lines
#     (1..line_count).each{|line|
#       # here we want to print out a pair
#       pair = []
#       pair_structure.each{|pr|
#         var_count, low, high = pr
#         unless var_count.is_number?
#           var_count = variable_values[var_count]
#         end
#         unless low.is_number?
#           low = variable_values[low]
#         end
#         unless high.is_number?
#           high = variable_values[high]
#         end
#
#         # build pair line
#         (0...var_count).each{||
#           pair << rnd.rand(low..high)
#         }
#         pair << "\n"
#       }
#       content_part = pair.join(' ')
#       puts content_part
#       file.puts content_part
#     }
#
#
#   }
# }
#
