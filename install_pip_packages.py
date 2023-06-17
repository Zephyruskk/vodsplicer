import sys, subprocess

required_libraries = [
    'Levenshtein', 
    'Pillow', 
    'pytesseract',
    'opencv-python',
    'google-api-python-client',
    'google-auth-oauthlib',
    'google-auth-httplib2',
    'oauth2client',
]

this_python = sys.executable

def install_library(module):
    subprocess.check_call([
        this_python,
        '-m',
        'pip',
        'install',
        module
    ])

if __name__ == '__main__':
    for m in required_libraries:
        install_library(m)