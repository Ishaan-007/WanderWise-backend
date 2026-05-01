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
                echo "=== Current directory on host ==="
                pwd
                echo "=== Files in current directory on host ==="
                ls -la
                
                docker run --rm \
                -u root \
                -v "$PWD:/workspace" \
                -w /workspace \
                python:3.10 bash -c "

                echo '=== Inside Docker Container ==='
                echo 'Current working directory:'
                pwd
                echo 'Contents of /workspace:'
                ls -la /workspace
                
                export PYTHONPATH=/workspace

                pip install --upgrade pip
                
                if [ -f /workspace/requirements.txt ]; then
                    echo 'Found requirements.txt'
                    pip install -r /workspace/requirements.txt
                else
                    echo 'requirements.txt not found in /workspace'
                    ls -la /workspace/
                    exit 1
                fi
                
                pip install pytest pytest-cov

                if [ -d /workspace/tests ]; then
                    echo 'Found tests directory'
                    pytest --cov=app --cov-report=xml /workspace/tests
                else
                    echo 'tests directory not found'
                    exit 1
                fi
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