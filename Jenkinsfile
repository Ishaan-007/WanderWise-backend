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
                rm -rf .scannerwork || true
                docker rm -f sonar-cli || true

                docker run --name sonar-cli \
                    -e SONAR_SCANNER_OPTS="-Xmx2048m -Xms512m" \
                    -v $(pwd):/usr/src \
                    --workdir /usr/src \
                    sonarsource/sonar-scanner-cli \
                    sonar-scanner \
                    -Dsonar.host.url=https://sonarcloud.io \
                    -Dsonar.token=$SONAR_TOKEN \
                    -Dsonar.projectKey=Ishaan-007_WanderWise-backend \
                    -Dsonar.organization=ishaan-007 \
                    -Dsonar.sources=app \
                    -Dsonar.tests=tests \
                    -Dsonar.python.version=3.10 \
                    -Dsonar.python.xunit.reportPath=coverage.xml \
                    -Dsonar.coverage.exclusions=tests/** \
                    -Dsonar.cpd.exclusions=tests/** \
                    -Dsonar.exclusions=**/__pycache__/**,**/*.pyc \
                    -Dsonar.analysis.detectedscm=git

                docker rm -f sonar-cli || true
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