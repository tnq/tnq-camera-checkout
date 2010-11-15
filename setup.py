VERSION = '0.0.1'

from setuptools import setup, find_packages

setup(
      name = 'tnq_checkout',
      version = VERSION,
      author = '',
      author_email = '',
      description = '',
      license = '',
      keywords = '',
      url = '',
      packages = find_packages(),
      include_package_data = True,
      package_data = {'' : ['*.cfg']},
      zip_safe = False,
      install_requires = ('nagare',),
      entry_points = """
      [nagare.applications]
      tnq_checkout = tnq_checkout.app:app
      """
     )
