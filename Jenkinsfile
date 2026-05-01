pipeline {
    agent any

    triggers {
        githubPush()
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t wanderwise-backend:latest .'
            }
        }

        stage('Run Tests (pytest)') {
            steps {
                sh '''
                # ADD THIS LINE: Clean up old containers first
                docker rm -f test-run || true

                docker run --name test-run \
                wanderwise-backend:latest \
                bash -c "
                python -m pytest --cov=app --cov-report=xml tests/
                "

                docker cp test-run:/app/coverage.xml .
                docker rm test-run
                '''
            }
        }

        stage('SonarCloud Analysis') {
            environment {
                SONAR_TOKEN = credentials('sonar-token')
            }
            steps {
                sh '''
                # 1. NUKE THE POISONED CACHE FROM PREVIOUS RUNS
                rm -rf .scannerwork || true
                
                # 2. Clean up old container
                docker rm -f sonar-cli || true
                
                # 3. Start container with max memory
                docker run -d --name sonar-cli \
                -e SONAR_SCANNER_OPTS="-Xmx4096m" \
                --entrypoint sh sonarsource/sonar-scanner-cli -c "tail -f /dev/null"
                
                # 4. Copy the freshly fixed code into the container
                docker cp . sonar-cli:/usr/src
                
                # 5. Execute scanner (EXCLUSIONS REMOVED)
                docker exec -w /usr/src sonar-cli sonar-scanner \
                -Dsonar.host.url=https://sonarcloud.io \
                -Dsonar.token=$SONAR_TOKEN \
                -Dsonar.projectKey=Ishaan-007_WanderWise-backend \
                -Dsonar.organization=ishaan-007 \
                -Dsonar.sources=app \
                -Dsonar.tests=tests \
                -Dsonar.python.coverage.reportPaths=coverage.xml \
                -Dsonar.python.version=3.10
                -Dsonar.exclusions="/*_2.py"
                
                # 6. Clean up
                docker rm -f sonar-cli
                '''
            }
        }

        stage('Run Container (Test)') {
            steps {
                sh '''
                docker rm -f test-container || true
                docker run -d -p 8000:8000 --name test-container wanderwise-backend:latest
                '''
            }
        }
    }
}