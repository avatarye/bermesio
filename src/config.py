class Config:
    """
    A singleton class that stores the configuration of the application.
    """

    app_version = '0.0.1'
    app_name = 'Bermesio'

    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

CONFIG = Config()