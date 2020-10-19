from setuptools import setup

setup(
    name='telebot',
    version='0.0.9',
    description='Group advertisement management and giveaway bot',
    author='Trenchguns',
    python_requires='>=3.6',
    install_requires=['wheel', 'python-telegram-bot', 'mysql-connector-python', 'gitdb', 'gitpython', 'alphabet_detector', 'emoji']
)
