pipeline {
    agent any

    tools {
        sonarScanner 'sonar-scanner'   // 👈 link Jenkins-installed scanner
    }

    stages {

        stage('Checkout Code') {
            steps {
                checkout scm
            }
        }

        stage('SonarCloud Analysis') {
            environment {
                SONAR_TOKEN = credentials('sonar-token')
            }
            steps {
                sh '''
                sonar-scanner \
                -Dsonar.projectKey=Ishaan-007_WanderWise-backend \
                -Dsonar.organization=Ishaan-007 \
                -Dsonar.sources=. \
                -Dsonar.host.url=https://sonarcloud.io \
                -Dsonar.login=$SONAR_TOKEN
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