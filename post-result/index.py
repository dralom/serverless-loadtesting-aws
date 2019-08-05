try:
  from .. import unzip_requirements
except ImportError:
  pass


def start(event, context):
    print(event)
    return None