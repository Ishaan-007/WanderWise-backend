pipeline {
    agent any

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
                # 1. Clean up any leftover container from previous failed runs
                docker rm -f sonar-cli || true
                
                # 2. Start the SonarScanner container in the background, keeping it alive
                docker run -d --name sonar-cli --entrypoint sh sonarsource/sonar-scanner-cli -c "tail -f /dev/null"
                
                # 3. Copy the entire Jenkins workspace (code + coverage.xml) into the container
                docker cp . sonar-cli:/usr/src
                
                # 4. Execute the scanner inside the container
                docker exec -w /usr/src sonar-cli sonar-scanner \
                -Dsonar.host.url=https://sonarcloud.io \
                -Dsonar.token=$SONAR_TOKEN \
                -Dsonar.projectKey=Ishaan-007_WanderWise-backend \
                -Dsonar.organization=ishaan-007 \
                -Dsonar.sources=app \
                -Dsonar.tests=tests \
                -Dsonar.python.coverage.reportPaths=coverage.xml
                
                # 5. Clean up the container
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