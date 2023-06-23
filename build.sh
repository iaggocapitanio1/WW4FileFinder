export VERSION=1.1.0
export PROJECT="file-watcher"
export USERNAME="iaggo"
export REPOSITORY="file-watcher"

docker build -t ${REPOSITORY} .

docker image tag ${REPOSITORY} ${USERNAME}/${REPOSITORY}:${VERSION}

docker image  push  ${USERNAME}/${REPOSITORY}:${VERSION}
