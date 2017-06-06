# TODO: Add NaiveTestCaseValidator

# test out the testcases by running a PYTHON solution of the challenge
require 'timeout'

class NaiveTestCaseValidator
  attr_reader :program_output

  # @param [String] input - the input string
  # @param [String] file_name - the name of the file we're testing
  # @param [Fixnum] timeout_seconds - the maximum amount of seconds this run is allowed  to run
  # @param [Boolean] to_pass - a boolean indicating if we want the given test to pass
  def initialize(input, file_name, timeout_seconds, to_pass)
    @input = input
    @file_name = file_name
    @timeout_seconds = timeout_seconds
    @to_pass = to_pass
    @timed_out = false
    @program_output = NIL
  end

  def run_program
    IO.popen "python3 #{@file_name}", 'r+' do |io|
      begin
        Timeout.timeout(@timeout_seconds) do
          io.puts @input
          result = ""
          line = io.gets
          while line
            result += line
            line = io.gets
          end
          @program_output = result
        end
      rescue Timeout::Error
        @timed_out = true
      end
    end
  end

  # Runs the program
  # @return [Bool] - indicating if the result is as desired
  def validate
    run_program
    @timed_out != @to_pass
  end
end
