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
                -e MONGO_URI="mongodb://localhost:27017/test_database" \
                wanderwise-backend:latest \
                bash -c "python -m pytest --cov=app --cov-report=xml tests/"
                
                docker cp test-run:/app/coverage.xml .
                docker rm test-run
                '''
            }
        }

        stage('Static Code Analysis') {
            steps {
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_KEY')]) {
                    sh """
                    echo "--- Cleaning up old files and containers ---"
                    rm -f sonar-project.properties || true
                    docker rm -f sonar-scan || true
                    
                    echo "--- Fixing XML Coverage Paths ---"
                    # Precision fix: Force the XML to point to the exact app folder in the scanner
                    sed -i 's|<source>.*</source>|<source>/usr/src/app</source>|g' coverage.xml
                    
                    echo "--- Bypassing Docker-in-Docker Bug via Copy ---"
                    docker create --name sonar-scan \
                    --network host \
                    -w /usr/src \
                    -e SONAR_SCANNER_OPTS="-Xmx512m" \
                    sonarsource/sonar-scanner-cli \
                    -Dsonar.projectKey=Wanderwise-Backend \
                    -Dsonar.sources=app \
                    -Dsonar.host.url=http://localhost:9000 \
                    -Dsonar.login=${SONAR_KEY} \
                    -Dsonar.python.coverage.reportPaths=coverage.xml \
                    -Dsonar.scm.disabled=true \
                    -Dsonar.python.version=3

                    docker cp . sonar-scan:/usr/src/
                    docker start -a sonar-scan
                    docker rm -f sonar-scan
                    """
                }
            }
        }

        stage('Deploy Observability Stack') {
            steps {
                withCredentials([string(credentialsId: 'MONGO_URI_SECRET', variable: 'DB_URI')]) {
                    sh '''
                    docker network create wanderwise-net || true
                    docker rm -f wanderwise-app || true
                    docker run -d --name wanderwise-app --network wanderwise-net -p 8000:8000 -e MONGO_URI="$DB_URI" wanderwise-backend:latest

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

                    docker volume create grafana-storage || true
                    docker rm -f grafana || true
                    docker run -d --name grafana --network wanderwise-net -p 3000:3000 -v grafana-storage:/var/lib/grafana grafana/grafana
                    '''
                }
            }
        }
    }
}