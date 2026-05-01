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
                docker run --rm \
                wanderwise-backend:latest \
                bash -c "

                echo '=== Inside container ==='
                ls -la

                pip install pytest pytest-cov

                python -m pytest -v --tb=short --cov=app --cov-report=xml tests/

                "
                '''
            }
        }

        stage('SonarCloud Analysis') {
            environment {
                SONAR_TOKEN = credentials('sonar-token')
            }
            steps {
                sh '''
                docker run --rm \
                -e SONAR_HOST_URL=https://sonarcloud.io \
                -e SONAR_TOKEN=$SONAR_TOKEN \
                wanderwise-backend:latest \
                bash -c "
                sonar-scanner \
                -Dsonar.projectKey=Ishaan-007_WanderWise-backend \
                -Dsonar.organization=ishaan-007 \
                -Dsonar.sources=app \
                -Dsonar.tests=tests \
                -Dsonar.python.coverage.reportPaths=coverage.xml
                "
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