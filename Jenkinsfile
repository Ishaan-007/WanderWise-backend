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