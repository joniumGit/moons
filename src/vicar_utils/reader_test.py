from src.vicar_utils import vicar_reader as vr

int_array = r"(1, 2, 3, 4, 5, 6, 843)"
float_array = r"(+1325.21312,-1321312.232,-1232.123,0.0001,00.00213E-1,132.3232E+3,132312.001E1)"
text_array = r"('hello world', hello world, fello, 'fellos', hi, '124455')"

for i in vr._process_value(int_array):
    try:
        assert isinstance(i, int)
    except AssertionError as e:
        print(type(i))
        print(i)
        raise e

for i in vr._process_value(float_array):
    try:
        assert isinstance(i, float)
    except AssertionError as e:
        print(type(i))
        print(i)
        raise e

for i in vr._process_value(text_array):
    try:
        assert isinstance(i, str)
    except AssertionError as e:
        print(type(i))
        print(i)
        raise e
