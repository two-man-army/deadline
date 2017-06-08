require_relative 'input_parser'
require_relative 'test_case_generator'

ip = InputParser.new
input_content = ip.parse_input
puts 'Do you have two solutions (good solution and naive)? (y/n)'
test_case_count = 12
ans = gets.chomp
puts 'Allow duplicates?'
allow_duplicates = if gets.chomp == 'y' then true else false end
if ans.include? 'y'
  puts 'How many (in percentage) test cases do you want to pass with the naive solution?'
  percentage = gets.chomp
  if not percentage.is_number? or percentage.to_i < 0 or percentage.to_i > 100
    raise Exception('INVALID PERCENTAGE')
  end
  test_gen = GoodAndNaiveTestCaseGenerator.new(
    test_case_count, 5, input_content, 'stone_naive.py',
    'stone_good.py', percentage.to_i, allow_duplicates)
else
  test_gen = NaiveTestCaseGenerator.new(1, 5, input_content, 'luck_balance.py', allow_duplicates)
end
test_gen.generate
