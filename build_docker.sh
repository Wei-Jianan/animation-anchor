set -uexo pipefail
IMAGE_NAME=animation_anchor:v1.0
python setup.py bdist_wheel
docker build . -t  ${IMAGE_NAME}
docker save ${IMAGE_NAME} -o animation_anchor.tar