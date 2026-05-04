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
                # Clean up any old test containers
                docker rm -f test-run || true
                
                # Run tests and generate the coverage report
                docker run --name test-run \
                -e MONGO_URI="mongodb://localhost:27017/test_database" \
                wanderwise-backend:latest \
                bash -c "python -m pytest --cov=app --cov-report=xml tests/"
                
                # Copy the report to the workspace for SonarScanner to find
                docker cp test-run:/app/coverage.xml .
                docker rm test-run
                '''
            }
        }

        stage('Static Code Analysis') {
            steps {
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_KEY')]) {
                    sh """
                    echo "--- Cleaning up sonar-project.properties ---"
                    sed -i '/sonar.login/d' sonar-project.properties || true
                    
                    echo "--- Starting SonarScanner ---"
                    docker run --rm \
                    --network host \
                    -v \$(pwd):/usr/src \
                    -e SONAR_SCANNER_OPTS="-Xmx512m" \
                    sonarsource/sonar-scanner-cli \
                    -Dsonar.projectKey=Wanderwise-Backend \
                    -Dsonar.sources=. \
                    -Dsonar.exclusions=tests/**,env/**,venv/**,**/__pycache__/**,*.xml,prometheus_temp.yml \
                    -Dsonar.host.url=http://localhost:9000 \
                    -Dsonar.login=${SONAR_KEY} \
                    -Dsonar.python.coverage.reportPaths=coverage.xml \
                    -Dsonar.scm.disabled=true \
                    -Dsonar.python.version=3
                    """
                }
            }
        }

        stage('Deploy Observability Stack') {
            steps {
                withCredentials([string(credentialsId: 'MONGO_URI_SECRET', variable: 'DB_URI')]) {
                    sh '''
                    # 1. Setup Network
                    docker network create wanderwise-net || true
                    
                    # 2. Deploy App
                    docker rm -f wanderwise-app || true
                    docker run -d --name wanderwise-app --network wanderwise-net -p 8000:8000 -e MONGO_URI="$DB_URI" wanderwise-backend:latest

                    # 3. Setup Prometheus
                    cat <<EOF > prometheus_temp.yml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'wanderwise-backend'
    static_configs:
      - targets: ['wanderwise-app:8000']
EOF
                    docker rm -f prometheus || true
                    docker run -d --name prometheus --network wanderwise-net -p 9090:9090 prom/prometheus
                    sleep 2
                    docker cp prometheus_temp.yml prometheus:/etc/prometheus/prometheus.yml
                    docker restart prometheus

                    # 4. Setup Grafana
                    docker volume create grafana-storage || true
                    docker rm -f grafana || true
                    docker run -d --name grafana --network wanderwise-net -p 3000:3000 -v grafana-storage:/var/lib/grafana grafana/grafana
                    '''
                }
            }
        }
    }
}