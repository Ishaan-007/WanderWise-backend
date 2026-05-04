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
                # 1. Create a shared network
                docker network create wanderwise-net || true

                # 2. Start the WanderWise App
                docker rm -f wanderwise-app || true
                docker run -d \
                  --name wanderwise-app \
                  --network wanderwise-net \
                  -p 8000:8000 \
                  wanderwise-backend:latest

                # 3. Create a temporary config file on the host machine
                # (Jenkins will write this into the current workspace)
                cat <<EOF > prometheus_temp.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'wanderwise-backend'
    static_configs:
      - targets: ['wanderwise-app:8000']
EOF

                # 4. Start Prometheus (Using a slightly different mount method)
                docker rm -f prometheus || true
                
                # We use docker cp to push the file into the container AFTER it starts
                # This bypasses the volume mapping issue entirely.
                docker run -d \
                  --name prometheus \
                  --network wanderwise-net \
                  -p 9090:9090 \
                  prom/prometheus
                  
                # Wait 2 seconds for Prometheus to spin up, then inject the config
                sleep 2
                docker cp prometheus_temp.yml prometheus:/etc/prometheus/prometheus.yml
                
                # Restart Prometheus to apply the new config
                docker restart prometheus

                # 5. Start Grafana
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