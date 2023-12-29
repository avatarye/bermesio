import pickle
import dill


def is_dillable(obj):
    try:
        dill.dumps(obj)
        return True
    except:
        return False
