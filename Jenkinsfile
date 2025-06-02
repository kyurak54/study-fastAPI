pipeline {
    agent any

    environment {
        // --- Jenkins Agent (빌드 환경) 관련 변수 ---
        GIT_CREDENTIALSID = "github_token"
        GIT_URL           = "https://github.com/kyurak54/study-fastapi.git"
        GIT_BRANCH        = "main"

        // --- Docker Registry (GHCR) 관련 변수 ---
        DOCKER_REGISTRY   = "ghcr.io"
        GITHUB_USERNAME   = "kyurak54" // 🔧 수정: 일관된 변수명 사용
        APP_NAME          = "study-fastapi"
        DOCKER_IMAGE_NAME = "${DOCKER_REGISTRY}/${GITHUB_USERNAME}/${APP_NAME}"
        DOCKER_TAG        = "${env.BUILD_NUMBER}"
        DOCKER_FULL_IMAGE = "${DOCKER_IMAGE_NAME}:${DOCKER_TAG}"
        DOCKER_CREDS_ID   = "github_token"

        // --- WAS 서버 (배포 대상) 관련 변수 ---
        WAS_USER          = "pwas"
        WAS_HOST          = "10.126.80.146"
        WAS_SSH_CREDS_ID  = "wa"
        WAS_APP_PATH      = "/home/${WAS_USER}/${APP_NAME}"

        // --- 이미지 정리 설정 ---
        KEEP_LATEST_COUNT = 2
    }

    stages {
        stage('📥 Git Clone') {
            steps {
                script {
                    echo "Git Repository: ${GIT_URL}, Branch: ${GIT_BRANCH}"
                    sh 'ls -al'
                }
            }
        }

        stage('🛠️ Build Docker Image'){
            steps {
                script {
                    echo "--- Docker 이미지 빌드 시작: ${DOCKER_FULL_IMAGE} ---"
                    sh "docker build -t ${DOCKER_FULL_IMAGE} ."
                    echo "--- 빌드된 이미지 확인 ---"
                    sh "docker images ${DOCKER_REGISTRY}/${GITHUB_USERNAME}/${APP_NAME}"
                }
            }
        }

        stage('📤 Push Docker Image to GHCR') {
            steps {
                // 🔧 수정: 변수명을 GITHUB_USERNAME으로 통일
                withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDS_ID}", usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GH_TOKEN')]) {
                    sh '''
                        echo "$GH_TOKEN" | docker login $DOCKER_REGISTRY -u "$GITHUB_USERNAME" --password-stdin
                        docker push $DOCKER_FULL_IMAGE
                        docker logout $DOCKER_REGISTRY
                    '''
                }
            }
        }
        
        stage('🧹 Cleanup Docker Images (Jenkins)') {
            steps {
                script {
                    def imageToClean = "${DOCKER_IMAGE_NAME}"
                    sh """
                        echo "[Jenkins] 오래된 이미지 2개만 남기고 삭제"
                        docker images --format '{{.Repository}}:{{.Tag}}' \\
                            | grep "^${imageToClean}:" \\
                            | sort -t':' -k2Vr \\
                            | tail -n +3 \\
                            | xargs -r docker rmi || echo "삭제할 이미지가 없습니다"
                        echo "[Jenkins] 이미지 정리 완료"
                    """
                }
            }
        }

        stage('🚀 Deploy and Run on WAS') {
            steps {
                // 🔧 수정: SSH 블록에서 사용할 변수들을 미리 정의
                script {
                    def dockerRegistry = "${DOCKER_REGISTRY}"
                    def githubUsername = "${GITHUB_USERNAME}"
                    def imageToClean = "${DOCKER_IMAGE_NAME}"
                    def fullImage = "${DOCKER_FULL_IMAGE}"
                    def appName = "${APP_NAME}"
                    
                    // 🔧 수정: withCredentials와 sshagent를 중첩해서 사용
                    withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDS_ID}", usernameVariable: 'GITHUB_USERNAME', passwordVariable: 'GH_TOKEN')]) {
                        sshagent(credentials: ['wa']) {
                            sh """
                                ssh -o StrictHostKeyChecking=no ${WAS_USER}@${WAS_HOST} <<'EOF'
                                set -e

                                echo "[INFO] WAS 서버에서 GHCR 로그인 시작"
                                echo "${GH_TOKEN}" | docker login ${dockerRegistry} -u "${githubUsername}" --password-stdin
                                echo "[INFO] WAS 서버에서 GHCR 로그인 성공"

                                echo "[WAS] Docker pull ⇒ ${fullImage}"
                                docker pull "${fullImage}"

                                echo "[WAS] 기존 컨테이너 정리"
                                docker rm -f "${appName}" 2>/dev/null || true

                                echo "[WAS] 새 컨테이너 실행"
                                docker run -d --name "${appName}" -p 18000:8000 -v /etc/localtime:/etc/localtime:ro -e TZ=Asia/Seoul "${fullImage}"

                                echo "[WAS] 오래된 이미지 2개만 남기고 삭제"
                                docker images --format '{{.Repository}}:{{.Tag}}' \\
                                    | grep "^${imageToClean}:" \\
                                    | sort -t':' -k2Vr \\
                                    | tail -n +3 \\
                                    | xargs -r docker rmi || echo "삭제할 이미지가 없습니다"

                                echo "[WAS] 이미지 정리 완료"

                                echo "[INFO] WAS 서버에서 GHCR 로그아웃"
                                docker logout ${dockerRegistry}
                                
EOF
                            """
                        }
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