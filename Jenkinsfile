pipeline {
    agent any

    stages {

        stage('SonarCloud Analysis') {
            steps {
                sh '''
                if command -v sonar-scanner >/dev/null 2>&1; then
                    sonar-scanner \
                    -Dsonar.organization=Ishaan-007 \
                    -Dsonar.projectKey=WanderWise-backend \
                    -Dsonar.sources=. \
                    -Dsonar.host.url=https://sonarcloud.io \
                    -Dsonar.login=$SONAR_TOKEN
                else
                    echo "SonarScanner not installed, skipping analysis"
                fi
                '''
            }
        }

        stage('Run Tests (pytest)') {
            agent {
                docker {
                    image 'python:3.10'
                }
            }
            steps {
                sh '''
                export PYTHONPATH=$PYTHONPATH:.
                
                python -m venv venv
                . venv/bin/activate
                
                pip install --upgrade pip
                pip install -r requirements.txt
                pip install pytest
                
                pytest
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