docker buildx use mybuilder

docker buildx build --platform linux/amd64,linux/arm64 -t xiaokuidocker/codeinterpreter:base-tag -f Dockerfile --target base --push .

docker buildx build --platform linux/amd64,linux/arm64 -t xiaokuidocker/codeinterpreter:build-tag -f Dockerfile --target build --push .

docker buildx build --platform linux/amd64,linux/arm64 -t xiaokuidocker/codeinterpreter:latest -f Dockerfile --target runtime --push .
