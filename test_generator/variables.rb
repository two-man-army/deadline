# The Variable classes
FACTORS = {}

class Integer
  def factors
    if FACTORS.include? self
      return FACTORS[self]
    end

    FACTORS[self] = 1.upto(Math.sqrt(self)).select {|i| (self % i).zero?}.inject([]) do |f, i|
      f << i
      f << self / i unless i == self / i
      f
    end
  end


end

class Variable
  # factor_of - a number we want this variable to be a factor of
  # factor_percentage - a percentage - the chance we want this to be a factor
  attr_accessor :factor_of, :factor_percentage

  def get_factor_of_value
    return NIL if @factor_of.nil?
    factor = @factor_of
    if @factor_of.is_a? Variable
      @factor_of.gen_value(Random.new) if @factor_of.value.nil?
      factor = @factor_of.value
    end
    factor
  end

  # return a boolean indicating fi we want this number to be a factor
  def to_be_a_factor?
    return false if @factor_percentage.nil? || @factor_of.nil?
    Random.new().rand(1..100) <= @factor_percentage
  end

  def fetch_min_max_values
    min_value = if @min.is_a? Variable then @min.value else @min end
    max_value = if @max.is_a? Variable then @max.value else @max end
    [min_value, max_value]
  end

  def generate_value(rnd_obj, to_be_a_factor)
    factor = get_factor_of_value
    min, max = fetch_min_max_values
    if to_be_a_factor
      @value = factor.factors.sample
    else
      @value = rnd_obj.rand(min..max)
    end
  end

  def gen_value(rnd_obj)
    to_be_a_factor = to_be_a_factor?

    generate_value(rnd_obj, to_be_a_factor)
    until is_valid_value?(to_be_a_factor)
      generate_value(rnd_obj, to_be_a_factor)
    end
    @value
  end

  def gen_harder_value(rnd_obj)
    to_be_a_factor = to_be_a_factor?

    generate_harder_value(rnd_obj, to_be_a_factor)
    until is_valid_value?(to_be_a_factor)
      generate_harder_value(rnd_obj, to_be_a_factor)
    end
    @value
  end

  # Generates a higher value
  def generate_harder_value(rnd_obj, _)
    # generate from the top 70% upwards
    min, max = fetch_min_max_values
    diff = max-min
    top_seventy_percent = 0.7 * diff
    @value = rnd_obj.rand(Integer(top_seventy_percent)..max)
  end

  def is_valid_value?(to_be_a_factor)
    return false if @value.nil?
    min_value, max_value = fetch_min_max_values

    is_in_range = @value >= min_value && @value <= max_value
    divisible = true
    factor = if @factor_of.is_a? Variable then @factor_of.value else @factor_of end
    if to_be_a_factor
      divisible = factor % @value == 0
    end
    is_in_range && divisible
  end
end

# Holds a constant variable which depends on constant values
class IndependantVariable < Variable
  attr_accessor :value
  def initialize(value = NIL, min = NIL, max = NIL, factor_of = NIL)
    @name = NIL
    @value = value
    @min = min
    @max = max
    @factor_of = factor_of
  end

end


# Holds a variable that depends on other values
class DependantVariable < Variable
  def initialize(name = NIL, value = NIL, min = NIL, max = NIL, factor_of = NIL)
    @name = name
    @value = value # should be a Variable instance
    @min = min
    @max = max
    @factor_of = factor_of
  end

  def value
    raise Exception("#{@name}'s value is not generated!") if @value.nil?

    @value
  end
end
