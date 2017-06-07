require_relative 'test_case_validator'

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
      gen = InputGenerator.new(@input_content)
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
      gen = InputGenerator.new(@input_content, gen_harder)
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