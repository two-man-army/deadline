# The Variable classes
class Integer
  def factors
    1.upto(Math.sqrt(self)).select {|i| (self % i).zero?}.inject([]) do |f, i|
      f << i
      f << self / i unless i == self / i
      f
    end.sort
  end
end

class Variable
  attr_accessor :factor_of

  def get_factor_of_value
    return NIL if @factor_of.nil?
    factor = @factor_of
    if @factor_of.is_a? Variable
      @factor_of.gen_value(Random.new) if @factor_of.value.nil?
      factor = @factor_of.value
    end
    factor
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

  def generate_value(rnd_obj)
    factor = get_factor_of_value
    if factor.nil?
      @value = rnd_obj.rand(@min..@max)
    else
      @value = factor.factors.sample
    end
  end

  # Generates a higher value
  def generate_harder_value(rnd_obj)
    # generate from the top 70% upwards
    diff = @max-@min
    top_seventy_percent = 0.7 * diff
    @value = rnd_obj.rand(Integer(top_seventy_percent)..@max)
  end

  def gen_value(rnd_obj)
    generate_value(rnd_obj)

    until is_valid_value?
      generate_value(rnd_obj)
    end
    @value
  end

  def gen_harder_value(rnd_obj)
    generate_harder_value(rnd_obj)
    until is_valid_value?
      generate_harder_value(rnd_obj)
    end
    @value
  end

  def is_valid_value?
    return false if @value.nil?
    min_value = @min
    max_value = @max

    min_value = @min.value if @min.is_a? Variable
    max_value = @max.value if @max.is_a? Variable
    is_in_range = @value >= min_value && @value <= max_value
    divisible = true
    unless @factor_of.nil?

      divisible = factor.value % @value == 0
    end
    is_in_range && divisible
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

  def generate_value(rnd_obj)
    factor = get_factor_of_value
    if factor.nil?
      min_value = @min
      max_value = @max

      min_value = @min.value if @min.is_a? Variable
      max_value = @max.value if @max.is_a? Variable

      @value = rnd_obj.rand(min_value..max_value)
    else
      @value = factor.factors.sample
    end
  end
  # Generates a higher value
  def generate_harder_value(rnd_obj)
    min_value = @min
    max_value = @max
    # generate from the top 70% upwards
    min_value = @min.value if @min.is_a? Variable
    max_value = @max.value if @max.is_a? Variable
    diff = max_value-min_value
    top_seventy_percent = 0.7 * diff
    @value = rnd_obj.rand(Integer(top_seventy_percent)..max_value)
  end


  def gen_harder_value(rnd_obj)
    generate_harder_value(rnd_obj)

    until is_valid_value?
      generate_harder_value(rnd_obj)
    end
    @value
  end

  def gen_value(rnd_obj)
    generate_harder_value(rnd_obj)

    until is_valid_value?
      generate_value(rnd_obj)
    end
    @value
  end

  def is_valid_value?
    return false if @value.nil?
    min_value = @min
    max_value = @max

    min_value = @min.value if @min.is_a? Variable
    max_value = @max.value if @max.is_a? Variable
    is_in_range = @value >= min_value && @value <= max_value
    divisible = true
    unless @factor_of.nil?
      factor = @factor_of
      if @factor_of.is_a? Variable
        @factor_of.gen_value(Random.new) if @factor_of.value.nil?
        factor = @factor_of.value
      end
      divisible = factor % @value == 0
    end
    is_in_range && divisible
  end
end
