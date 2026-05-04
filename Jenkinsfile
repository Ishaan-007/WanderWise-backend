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

        stage('Deploy Observability Stack') {
            steps {
                sh '''
                # 1. Create a shared network so the containers can talk to each other
                docker network create wanderwise-net || true

                # 2. Start the WanderWise App
                docker rm -f wanderwise-app || true
                docker run -d \
                  --name wanderwise-app \
                  --network wanderwise-net \
                  -p 8000:8000 \
                  wanderwise-backend:latest

                # 3. Start Prometheus (Mounting the config file from your repo)
                docker rm -f prometheus || true
                docker run -d \
                  --name prometheus \
                  --network wanderwise-net \
                  -p 9090:9090 \
                  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
                  prom/prometheus

                # 4. Start Grafana
                docker rm -f grafana || true
                docker run -d \
                  --name grafana \
                  --network wanderwise-net \
                  -p 3000:3000 \
                  grafana/grafana
                '''
            }
        }
    }
}