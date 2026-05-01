pipeline {
    agent any

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('Run Tests (pytest)') {
            steps {
                sh '''
                docker run --rm \
                -u root \
                -v "$PWD:/app" \
                -w /app \
                python:3.10 bash -c "

                export PYTHONPATH=.

                python -m venv venv
                . venv/bin/activate

                pip install --upgrade pip
                if [ ! -f requirements.txt ]; then echo 'requirements.txt not found'; exit 1; fi
                pip install -r requirements.txt
                pip install pytest pytest-cov

                if [ ! -d tests ]; then echo 'tests directory not found'; exit 1; fi
                pytest --cov=app --cov-report=xml tests
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
                -v "$PWD:/usr/src" \
                -w /usr/src \
                sonarsource/sonar-scanner-cli \
                -Dsonar.projectKey=Ishaan-007_WanderWise-backend \
                -Dsonar.organization=ishaan-007 \
                -Dsonar.sources=app \
                -Dsonar.tests=tests \
                -Dsonar.python.version=3.10 \
                -Dsonar.scm.provider=git \
                -Dsonar.python.coverage.reportPaths=coverage.xml
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t wanderwise-backend .'
            }
        }

        stage('Run Container (Test)') {
            steps {
                sh '''
                docker rm -f test-container || true
                docker run -d -p 8000:8000 --name test-container wanderwise-backend
                '''
            }
        }
    }
}