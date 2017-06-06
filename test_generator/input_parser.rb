# Currently only works with INTEGER numbers

# Reads input from the user
class Object
  def is_number?
    self.to_f.to_s == self.to_s || self.to_i.to_s == self.to_s
  end
end

puts 'Enter the total amount of test cases you want'
test_case_count = gets.chomp.to_i

puts 'Currently building: SETUP FORM. This is where you set up various variables to' +
     'later reference and impose limits with.'

puts 'Enter the number of input lines'
input_line_count = gets.to_i
variable_limits = {}
variable_structure = []  # hold the order of the variables to come
(1..input_line_count).each {|line|
  puts "Line #{line}, enter the name of the variables, separated by space"
  variables = gets.split
  puts "Your variables are: #{variables}"
  variable_structure << variables
  variables.each {|var|
    # TODO: add upper/lower limit be another variable
    puts "Enter the lower limit for variable #{var.upcase}"
    lower_limit = gets.to_i
    puts "Enter the upper limit for variable #{var.upcase}"
    upper_limit = gets.to_i

    variable_limits[var] = [lower_limit, upper_limit]  # TODO: Maybe convert var to a class?
  }
}

puts 'Currently building: CONTENT FORM. This is the meat of the input'
puts 'Enter the number of lines that will constitute a single pair of input line (can be another variable)'
pair_lines_count = gets.chomp
puts pair_lines_count.is_number?
if pair_lines_count.is_number?
  pair_lines_count = pair_lines_count.to_i
end
puts 'Enter the number of overall lines you will have (can be another variable)'
line_count = gets.chomp
if line_count.is_number?
  line_count = line_count.to_i
end

# build each pair's limits
pair_structure = []
(1..pair_lines_count).each {|pair|
  # build an array
  puts "Pair line #{pair}, enter the number of the variables"
  var_count = gets.chomp
  if var_count.is_number?
    var_count = var_count.to_i
  end
  puts "Enter lower limit for each number"
  low_limit = gets.chomp
  if low_limit.is_number?
    low_limit = low_limit.to_i
  end
  puts "Enter upper limit for each number"
  upp_limit = gets.chomp
  if upp_limit.is_number?
    upp_limit = upp_limit.to_i
  end
  pair_structure << [var_count, low_limit, upp_limit]
}

# TODO: get annexation part

rnd = Random.new

(0...test_case_count).each {|test|
  File.open("input_#{test}.txt", 'w') { |file|
    # start building output
    # INPUT PART
    variable_values = {}
    variable_structure.each{|line|
      output = []
      line.each{|var|
        # assign a value to the variable
        low, max = variable_limits[var]
        # some other variables are the limit
        unless low.is_number?
          low = variable_values[low]
        end
        unless max.is_number?
          max = variable_values[max]
        end
        variable_values[var] = rnd.rand(low..max)
        output << variable_values[var]
      }
      input_part = output.join(' ')
      puts input_part
      file.puts input_part
    }

    # CONTENT PART
    unless line_count.is_number?
      line_count = variable_values[var]
    end
    # build lines
    (1..line_count).each{|line|
      # here we want to print out a pair
      pair = []
      pair_structure.each{|pr|
        var_count, low, high = pr
        unless var_count.is_number?
          var_count = variable_values[var_count]
        end
        unless low.is_number?
          low = variable_values[low]
        end
        unless high.is_number?
          high = variable_values[high]
        end

        # build pair line
        (0...var_count).each{||
          pair << rnd.rand(low..high)
        }
        pair << "\n"
      }
      content_part = pair.join(' ')
      puts content_part
      file.puts content_part
    }


  }
}

