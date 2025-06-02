pipeline {
    // jenkins 에이전트 설정: Docker CLI가 설치된 에이전트에서 실행
    // 만약 jenkins 에이전트 자체가 Docker가 설치된 VM이라면 'agent any'를 사용해도 됨
    agent  any

    environment {
        // --- Jenkins Agent (빌드 환경) 관련 변수 ---
        GIT_CREDENTIALSID = "github_token"
        GIT_URL           = "https://github.com/kyurak54/study-fastapi.git"
        GIT_BRANCH        = "main" // 빌드할 Git 브랜치

        // --- Docker Registry (GHCR) 관련 변수 ---
        DOCKER_REGISTRY   = "ghcr.io"
        GITHUB_USERNAME   = "kyurak54" // 당신의 GitHub 사용자 이름
        APP_NAME          = "study-fastapi" // FastAPI 프로젝트 이름 (GHCR 레포지토리 이름으로 사용)
        DOCKER_IMAGE_NAME   = "${DOCKER_REGISTRY}/${GITHUB_USERNAME}/${APP_NAME}"
        DOCKER_TAG          = "${env.BUILD_NUMBER}"
        DOCKER_FULL_IMAGE   = "${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
        DOCKER_CREDS_ID     = "github_token"

        // --- WAS 서버 (배포 대상) 관련 변수 ---
        WAS_USER          = "pwas" // WAS 서버 SSH 사용자 이름
        WAS_HOST          = "10.126.80.146" // WAS 서버 IP 주소
        WAS_SSH_CREDS_ID  = "wa" // Jenkins Credential ID (WAS 서버 SSH 접속용)
        WAS_APP_PATH      = "/home/${WAS_USER}/${APP_NAME}" // WAS 서버 내에서 프로젝트가 배포될 경로

        // --- 이미지 정리 설정 ---
        KEEP_LATEST_COUNT = 2 // WAS 서버에 유지할 최신 이미지 개수 (최신 2개는 삭제하지 않음)
    }

    stages {
        stage('📥 Git Clone') {
            steps {
                script {
                    // Jenkins Pipeline SCM 설정에서 이미 Git 클론을 수행하므로,
                    // 추가적으로 이 스텝에서 git 명령을 명시할 필요는 없습니다.
                    // 만약 특정 서브모듈 등 추가 클론이 필요하다면 여기에 추가할 수 있습니다.
                    echo "Git Repository: ${GIT_URL}, Branch: ${GIT_BRANCH}"
                    // workspace 디렉토리 확인
                    sh 'ls -al'
                }
            }
        }

        stage('🛠️ Build Docker Image'){
            steps {
                script {
                    echo "--- Docker 이미지 빌드 시작: ${DOCKER_FULL_IMAGE} ---"
                    // Dockerfile은 Jenkins 작업 공간의 루트에 있어야 합니다.
                    sh "docker build -t ${DOCKER_FULL_IMAGE} ."
                    echo "--- 빌드된 이미지 확인 ---"
                    sh "docker images ${DOCKER_REGISTRY}/${GITHUB_USERNAME}/${APP_NAME}"
                }
            }
        }

        stage('📤 Push Docker Image to GHCR') {
            steps {
                // GitHub Container Registry로 이미지 푸시
                withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDS_ID}", usernameVariable: 'GH_USERNAME', passwordVariable: 'GH_TOKEN')]) {
                    sh '''
                        echo "$GH_TOKEN" | docker login $DOCKER_REGISTRY -u "$GH_USERNAME" --password-stdin
                        docker push $DOCKER_FULL_IMAGE
                        docker logout $DOCKER_REGISTRY
                    '''
                }
            }
        }
        
        stage('🧹 Cleanup Docker Images (Jenkins)') {
            steps {
                // Jenkins 서버에서 오래된 Docker 이미지 정리
                script {
                    def imageToClean = "${DOCKER_IMAGE_NAME}"
                    sh """
                        echo "[Jenkins] 오래된 이미지 2개만 남기고 삭제"
                        docker images --format '{{.Repository}}:{{.Tag}}' \\
                            | grep "^${imageToClean}:" \\
                            | sort -t':' -k2Vr \\
                            | tail -n +3 \\
                            | xargs -r docker rmi
                        echo "[Jenkins] 이미지 정리 완료"
                    """
                }
            }
        }

        stage('🚀 Deploy and Run on WAS') {
            steps {
                /* 1) GHCR 로그인에 필요한 PAT를 Jenkins 쉘 변수에만 주입  */
                withCredentials([usernamePassword(
                        credentialsId: "${DOCKER_CREDS_ID}",
                        usernameVariable: 'GH_USER',
                        passwordVariable: 'GH_PAT'
                )]) {

                    /* 2) SSH 비밀키로 원격 접속 */
                    sshagent(credentials: ['wa']) {

                        /* 3) Groovy 보간 금지(single-quoted ''' 블록) */
                        sh '''
                        echo "[Jenkins] WAS 서버로 배포 시작"

                        ## PAT를 SSH 원격 명령에 파이프로 전달 ##
                        echo "$GH_PAT" | ssh -o StrictHostKeyChecking=no $WAS_USER@$WAS_HOST bash -s -- <<'ENDSSH'
                        set -e
                        echo "[WAS] GHCR 로그인"
                        read -r PAT
                        echo "$PAT" | docker login $DOCKER_REGISTRY -u "$GH_USER" --password-stdin

                        echo "[WAS] 이미지 풀 ➜ $DOCKER_FULL_IMAGE"
                        docker pull "$DOCKER_FULL_IMAGE"

                        echo "[WAS] 컨테이너 정리"
                        docker rm -f "$APP_NAME" 2>/dev/null || true

                        echo "[WAS] 새 컨테이너 실행"
                        docker run -d --name "$APP_NAME" \
                                    -p 18000:8000 \
                                    -v /etc/localtime:/etc/localtime:ro \
                                    -e TZ=Asia/Seoul \
                                    "$DOCKER_FULL_IMAGE"

                        echo "[WAS] 오래된 이미지 정리"
                        docker images --format '{{.Repository}}:{{.Tag}}' |
                            grep "^$DOCKER_IMAGE_NAME:" |
                            sort -t':' -k2Vr |
                            tail -n +$((KEEP_LATEST_COUNT+1)) |
                            xargs -r docker rmi

                        docker logout $DOCKER_REGISTRY
                        EOSH
                        '''
                    }
                }
            }
        }
    }

        post {
            success {
                echo '✅ 배포 성공!'
            }
            failure {
                echo '❌ 배포 실패. 확인 필요.'
            }
            always {
                cleanWs()
            }
        }
}