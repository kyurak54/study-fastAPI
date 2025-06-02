pipeline {
    // jenkins 에이전트 설정: Docker CLI가 설치된 에이전트에서 실행
    // 만약 jenkins 에이전트 자체가 Docker가 설치된 VM이라면 'agent any'를 사용해도 됨
    agent  any

    environment {
        // --- Jenkins Agent (빌드 환경) 관련 변수 ---
        GIT_CREDENTIALSID = "github_token"
        GIT_URL           = "https://github.com/kyurak54/study-fastAPI.git"
        GIT_BRANCH        = "main" // 빌드할 Git 브랜치

        // --- Docker Registry (GHCR) 관련 변수 ---
        DOCKER_REGISTRY   = "ghcr.io"
        GITHUB_USERNAME   = "kyurak54" // 당신의 GitHub 사용자 이름
        APP_NAME          = "study-fastAPI" // FastAPI 프로젝트 이름 (GHCR 레포지토리 이름으로 사용)
        DOCKER_TAG        = "${env.BUILD_NUMBER}" // Jenkins 빌드 번호를 이미지 태그로 사용
        DOCKER_FULL_IMAGE = "${DOCKER_REGISTRY}/${GITHUB_USERNAME}/${APP_NAME}:${DOCKER_TAG}" // 완성된 이미지 이름 (예: ghcr.io/kyurak54/my-fastapi-api:123)
        DOCKER_CREDS_ID   = "github_token" // Jenkins Credential ID (GHCR 로그인 및 푸시용)

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
                    script {
                        // Jenkins Credentials에서 사용자 이름과 비밀번호(PAT)를 가져와 Docker 로그인
                        withCredentials([usernamePassword(credentialsId: "${DOCKER_CREDS_ID}", usernameVariable: 'GH_USERNAME', passwordVariable: 'GH_TOKEN')]) {
                            sh """
                                echo "--- Docker Login to ${DOCKER_REGISTRY} ---"
                                echo "$GH_TOKEN" | docker login $DOCKER_REGISTRY -u "$GH_USERNAME" --password-stdin || exit 1
                                echo "--- Pushing image: ${DOCKER_FULL_IMAGE} ---"
                                docker push ${DOCKER_FULL_IMAGE} || exit 1
                                echo "--- Docker Logout ---"
                                docker logout ${DOCKER_REGISTRY}
                            """
                        }
                    }
                }
            }

            stage('🚀 Deploy & Clean on WAS') {
                steps {
                    // WAS 서버에 SSH 접속용 Credentials 사용
                    sshagent(credentials: ["${WAS_SSH_CREDS_ID}"]) {
                        // SSH를 통해 WAS 서버에서 명령 실행
                        sh """
                            ssh ${WAS_USER}@${WAS_HOST} '
                                set -e # 명령어 실패 시 즉시 종료

                                echo "[INFO] WAS 서버에서 배포 및 정리 시작"
                                
                                # 1. GHCR에 로그인 (원격 WAS 서버에서)
                                # GHCR 로그인 정보는 환경 변수가 아닌 직접 주입해야 함 (Jenkins SSH에서 바로 전달 X)
                                # WAS 서버에 docker login 정보가 이미 캐시되어 있다면 이 단계 생략 가능
                                # 또는 WAS 서버에서 GitHub PAT를 환경 변수 등으로 관리하여 로그인

                                echo "[INFO] Docker pull 시작: ${DOCKER_FULL_IMAGE}"
                                docker pull "${DOCKER_FULL_IMAGE}"

                                echo "[INFO] 기존 컨테이너 종료 및 삭제"
                                docker stop "${APP_NAME}" || true
                                docker rm "${APP_NAME}" || true

                                echo "[INFO] 새 컨테이너 실행"
                                # 컨테이너 포트 8000:8000 매핑 (호스트 8000 -> 컨테이너 8000)
                                docker run -d --name "${APP_NAME}" -p 8000:8000 "${DOCKER_FULL_IMAGE}" || exit 1

                                echo "[INFO] 오래된 이미지 정리 시작"
                                TARGET_IMAGE_REPO="${DOCKER_REGISTRY}/${GITHUB_USERNAME}/${APP_NAME}"

                                # 현재 실행 중인 컨테이너에서 사용하는 이미지 태그 가져오기
                                CURRENTLY_USED_IMAGE_TAGS=\$(docker ps --format "{{.Image}}" | grep "${TARGET_IMAGE_REPO}:" | awk -F':' '{print \$NF}' || true)
                                echo "현재 사용 중인 이미지 태그: \$CURRENTLY_USED_IMAGE_TAGS"

                                # 해당 레포지토리의 모든 태그를 숫자로 역순 정렬 (BUILD_NUMBER 기반 태그에 적합)
                                ALL_TAGS=\$(docker images --format '{{.Tag}}' "${TARGET_IMAGE_REPO}" | sort -nr || true)
                                echo "모든 이미지 태그 (최신순): \$ALL_TAGS"

                                DELETE_TAGS=()
                                KEPT_COUNT=0
                                
                                for TAG in \${ALL_TAGS[@]}; do
                                    FULL_IMAGE="\${TARGET_IMAGE_REPO}:\${TAG}"
                                    # 1. 현재 이 빌드에서 새로 배포되는 이미지 태그는 무조건 유지
                                    # 2. 현재 WAS에서 컨테이너가 사용 중인 이미지 태그도 무조건 유지
                                    # 3. 위에 해당하지 않으면서, 아직 유지해야 할 최신 이미지 개수(KEEP_LATEST_COUNT)가 채워지지 않았다면 해당 이미지 유지
                                    if [[ "\$TAG" == "\$DOCKER_TAG" ]] || [[ "\$CURRENTLY_USED_IMAGE_TAGS" == *"\$TAG"* ]]; then
                                        echo "유지: 현재 배포되거나 사용 중인 태그 - \$FULL_IMAGE"
                                    elif (( KEPT_COUNT < ${KEEP_LATEST_COUNT} )); then
                                        echo "유지: 최신 ${KEEP_LATEST_COUNT}개 중 하나 - \$FULL_IMAGE"
                                        KEPT_COUNT=\$((KEPT_COUNT + 1))
                                    else
                                        # 그 외의 모든 이미지는 삭제 대상에 추가
                                        DELETE_TAGS+=("\$FULL_IMAGE")
                                    fi
                                done
                                
                                if [ \${#DELETE_TAGS[@]} -eq 0 ]; then
                                    echo "삭제할 오래된 이미지가 없습니다."
                                else
                                    echo "삭제할 이미지 목록: \${DELETE_TAGS[@]}"
                                    printf "%s\\n" "\${DELETE_TAGS[@]}" | xargs -r -I {} docker rmi {}
                                    echo "[INFO] 정리 완료"
                                fi
                            '
                        """
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
                cleanWs() // Jenkins 작업 공간 정리
            }
        }
}