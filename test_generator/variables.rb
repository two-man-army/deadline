# The Variable classes

class Variable
end

# Holds a constant variable which depends on constant values
class IndependantVariable < Variable
  attr_accessor :value
  def initialize(value = NIL, min = NIL, max = NIL)
    @name = NIL
    @value = value
    @min = min
    @max = max
  end

  def gen_value(rnd_obj)
    @value = rnd_obj.rand(@min..@max)
  end

  # Generates a higher value
  def gen_harder_value(rnd_obj)
    # generate from the top 70% upwards
    diff = @max-@min
    top_seventy_percent = 0.7 * diff
    @value = rnd_obj.rand(Integer(top_seventy_percent)..@max)
  end
end


# Holds a variable that depends on other values
class DependantVariable < Variable
  def initialize(name = NIL, value = NIL, min = NIL, max = NIL)
    @name = name
    @value = value # should be a Variable instance
    @min = min
    @max = max
  end

  def value
    raise Exception("#{@name}'s value is not generated!") if @value.nil?

    @value
  end

  def gen_value(rnd_obj)
    min_value = @min
    max_value = @max

    min_value = @min.value if @min.is_a? Variable
    max_value = @max.value if @max.is_a? Variable

    @value = rnd_obj.rand(min_value..max_value)
  end
end
