from enum import Enum


class MonokaiColors(Enum):
    """Monokai Colors"""
    background = '#272822'
    foreground = '#F8F8F2'
    comment = '#75715E'
    red = '#F92672'
    orange = '#FD971F'
    light_orange = '#E69F66'
    yellow = '#E6DB74'
    green = '#A6E22E'
    cyan = '#66D9EF'
    blue = '#268BD2'
    purple = '#AE81FF'
    dark_blue = '#006AE7'


class BColors(Enum):
    """Custom colors for this application"""
    background = MonokaiColors.background.value
    text = MonokaiColors.foreground.value
    sub_text = MonokaiColors.comment.value

    profile = MonokaiColors.red.value
    blender_setup = MonokaiColors.purple.value
    blender_program = MonokaiColors.orange.value
    blender_released_addon = MonokaiColors.light_orange.value
    blender_released_script = MonokaiColors.yellow.value
    blender_venv = MonokaiColors.green.value
    blender_dev_addon = MonokaiColors.blue.value
    blender_dev_script = MonokaiColors.dark_blue.value
    python_dev_library = MonokaiColors.cyan.value

    blender_orange = '#EA7600'
    blender_blue = '#265787'

    bermeio_yellow = '#F6CB4E'
    bermeio_blue = '#13A0F5'

    @classmethod
    def get_color_by_class(cls, class_) -> str:
        """
        Use input class's name to find a color in this class. Convert the camel case class name to snake case first.

        :param class_: a class object

        :return: a hex color string
        """
        class_name = class_.__name__
        class_name = ''.join(['_' + i.lower() if i.isupper() else i for i in class_name]).lstrip('_')
        if hasattr(cls, class_name):
            return getattr(cls, class_name).value
        # If not found, return the text color
        return cls.text.value
