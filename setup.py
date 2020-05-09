from setuptools import setup, find_packages


if __name__ == '__main__':
    setup(
        name='animation_anchor',
        version='1.0',
        packages=find_packages(),
        author='jianan wei, suntianwei',
        install_requires=['numpy', 'opencv-python', 'ffmpeg-python', 'jieba', 'pypinyin', 'scipy', 'av'],
        package_data={
            'animation_anchor': [
                'assets/mapping_table/*',
                'assets/template/aide/*',
                'assets/viseme/aide/*/*',
                'assets/template/kuailepingan/*',
                'assets/viseme/kuailepingan/*/*',
                'htkaligner/model/*',
                'htkaligner/model/*/*',

            ]
        }

    )