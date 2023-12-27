from functools import wraps
import os
from pathlib import Path

import dill


class ObjectPool:
    """
    A global object pool that stores objects that are created with the pooled_class decorator, which is used to avoid
    creating duplicate objects based on the same class instantiate arguments. Some classes are expensive to create, like
    BlenderProgram, should use pooled_class decorator to be pooled in this ObjectPool.
    ObjectPool should be used as a static class, and should not be instantiated.
    ObjectPool also has save and load methods to save the object pool to disk as a dill file, and load the dill file
    from disk. This is to accelerate the startup time of the program, so the expensive objects don't need to be created
    again.
    """
    save_file_path = Path(__file__).parent / 'object_pool.dill'

    pool = {}

    def __new__(cls):
        """Guard against instantiation."""
        raise Exception('ObjectPool should not be instantiated.')

    @staticmethod
    def _get_object_pool_key(obj_cls, obj_args, obj_kwargs):
        """
        Get the key for the object pool by concatenate class name, init arguments, and init keyword arguments together.
        """
        obj_args_str = ','.join([str(arg) for arg in obj_args]).lower()
        obj_kwargs_str = ','.join([f'{key}={value}' for key, value in obj_kwargs.items()]).lower()
        return f'{obj_cls.__name__}|{obj_args_str}|{obj_kwargs_str}'

    @classmethod
    def add(cls, obj, obj_args, obj_kwargs):
        """Add an object to the pool, using the class, args and kwargs as the key."""
        pool_key = cls._get_object_pool_key(obj.__class__, obj_args, obj_kwargs)
        cls.pool[pool_key] = obj
        obj._pool_key = pool_key  # Adding pool_key as an attribute to the object for easy removal.
        cls.save()

    @classmethod
    def remove(cls, obj):
        """Remove an object from the pool using the pool_key attribute."""
        if getattr(obj, '_pool_key', None):
            del cls.pool[obj._pool_key]

    @classmethod
    def get(cls, obj_cls, obj_args, obj_kwargs):
        """Get an object from the pool using the class, args and kwargs as the key."""
        pool_key = cls._get_object_pool_key(obj_cls, obj_args, obj_kwargs)
        return cls.pool.get(pool_key, None)

    @classmethod
    def clear(cls):
        cls.pool = {}

    @classmethod
    def clear_save_file(cls):
        """Remove the dill file of object pool from disk."""
        if cls.save_file_path.exists():
            os.remove(cls.save_file_path)

    @classmethod
    def save(cls):
        """Save the object pool to disk as a dill file."""
        with open(cls.save_file_path, 'wb') as pickle_file:
            dill.dump(cls.pool, pickle_file)

    @classmethod
    def load(cls):
        """Load the dill file of object pool from disk."""
        if cls.save_file_path.exists():
            with open(cls.save_file_path, 'rb') as pickle_file:
                cls.pool = dill.load(pickle_file)


def pooled_class(cls):
    """
    A decorator that allows the class to be pooled in ObjectPool. It should be used with additional keyword argument
    "store_in_pool=True" when instantiating the class. This keyword argument will be removed before passing to the
    __init__ method. The comparison of whether two objects are the same is based on the class, args and kwargs passed to
    __init__ method.

    :param cls: the decorated class

    :return: the instance of the decorated class
    """
    @wraps(cls)
    def wrapper(*args, **kwargs):
        if 'store_in_pool' in kwargs:  # Pooling only happens when additional "store_in_pool" argument set to true.
            del kwargs['store_in_pool']  # Remove it from kwargs so it doesn't get passed to __init__.
            result = ObjectPool.get(cls, args, kwargs)  # Check if the object already exists in the pool.
            if result:
                return result
            else:
                object = cls(*args, **kwargs)
                ObjectPool.add(object, args, kwargs)
                return object
        else:  # If "store_in_pool" is not set, just create the object without pooling.
            object = cls(*args, **kwargs)
            return object
    return wrapper
