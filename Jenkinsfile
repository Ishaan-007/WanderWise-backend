pipeline {
    agent any

    stages {

        stage('Run Tests (pytest)') {
            agent {
                docker {
                    image 'python:3.10'
                }
            }
            steps {
                sh '''
                export PYTHONPATH=$PYTHONPATH:.
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