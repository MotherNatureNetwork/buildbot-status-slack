from distutils.core import setup

setup(
    name='buildbot_status_slack',
    version='1.0.0',
    author=['Sylvain Zimmer', 'Marten Klitzke', 'Raphael Randschau'],
    packages=['buildbot_status_slack'],
    scripts=[],
    url='https://github.com/mindmatters/buildbot-status-slack',
    license='LICENSE.txt',
    description='slack status plugin for buildbot',
    long_description=open('README.md').read(),
    install_requires=[
        "buildbot >= 0.8.0",
    ],
)