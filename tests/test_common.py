from bermesio.commons.common import blog


def test_logging():
    """ This is a test function for observing the output of the global logger. """
    blog(1, 'This is a debug message')
    blog(2, 'This is an info message')
    blog(3, 'This is a warning message')
    blog(4, 'This is an error message')
    blog(5, 'This is a critical message')
    assert True