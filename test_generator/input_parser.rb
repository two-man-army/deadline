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
    @value.value
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
    repeat_count = input_format.repeat_count
    if repeat_count.is_a? Variable
      repeat_count = repeat_count.value
    end
    output = []
    curr_output = []
    (0...repeat_count).each{||
      input_format.structure.each{|struct|
        # convert list of variables to a string
        output = struct.map {|var| var.gen_value(@rnd_obj)}
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
  def initialize(repeat_count=1, structure, name)
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


# create a sample input
# one N - count of array
# N elements array
N = IndependantVariable.new(value=NIL, min=100, max=1000)
N.gen_value(Random.new)
array_number = DependantVariable.new(name="arrNum", value=NIL, min=N, max=1000000000000)
initialization_phase = InputFormat.new(1, [[N]], "Initialization")
content_phase = InputFormat.new(1, [[array_number] * N.value], name="Array phase")
input_content = InputContent.new(initialization_phase, content_phase, NIL)
generator = Generator.new input_content
generator.generate













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
