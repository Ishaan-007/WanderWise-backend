pipeline {
    agent any

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout Code') {
            steps {
                checkout scm
                sh 'echo "--- Workspace Root Path: $(pwd) ---"'
            }
        }

        stage('Diagnostic: Check Workspace Structure') {
            steps {
                sh '''
                echo "--- Current Directory ---"
                pwd
                echo "--- Listing all files (recursive) ---"
                ls -R
                echo "--- Checking for sonar-project.properties ---"
                if [ -f sonar-project.properties ]; then
                    echo "Found sonar-project.properties. Content:"
                    cat sonar-project.properties
                else
                    echo "ERROR: sonar-project.properties NOT FOUND"
                fi
                '''
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
                echo "--- Cleaning up old test containers ---"
                docker rm -f test-run || true
                
                echo "--- Running Pytest and generating Coverage ---"
                docker run --name test-run \
                -e MONGO_URI="mongodb://localhost:27017/test_database" \
                wanderwise-backend:latest \
                bash -c "python -m pytest --cov=app --cov-report=xml tests/"
                
                echo "--- Extracting coverage.xml ---"
                docker cp test-run:/app/coverage.xml .
                
                echo "--- Verifying coverage.xml presence on host ---"
                ls -lh coverage.xml
                
                docker rm test-run
                '''
            }
        }

        stage('Static Code Analysis') {
            steps {
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_KEY')]) {
                    sh """
                    echo "--- Starting SonarScanner in DEBUG Mode (-X) ---"
                    docker run --rm \
                    -v \$(pwd):/usr/src \
                    -e SONAR_SCANNER_OPTS="-Xmx512m" \
                    sonarsource/sonar-scanner-cli \
                    -X \
                    -Dsonar.login=${SONAR_KEY} \
                    -Dsonar.verbose=true
                    """
                }
            }
        }

        stage('Deploy Observability Stack') {
            steps {
                withCredentials([string(credentialsId: 'MONGO_URI_SECRET', variable: 'DB_URI')]) {
                    sh '''
                    echo "--- Setting up Network and App ---"
                    docker network create wanderwise-net || true
                    docker rm -f wanderwise-app || true
                    docker run -d --name wanderwise-app --network wanderwise-net -p 8000:8000 -e MONGO_URI="$DB_URI" wanderwise-backend:latest

                    echo "--- Generating Prometheus Config ---"
                    cat <<EOF > prometheus_temp.yml
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'wanderwise-backend'
    static_configs:
      - targets: ['wanderwise-app:8000']
EOF
                    echo "--- Deploying Prometheus ---"
                    docker rm -f prometheus || true
                    docker run -d --name prometheus --network wanderwise-net -p 9090:9090 prom/prometheus
                    sleep 2
                    docker cp prometheus_temp.yml prometheus:/etc/prometheus/prometheus.yml
                    docker restart prometheus

                    echo "--- Deploying Grafana ---"
                    docker volume create grafana-storage || true
                    docker rm -f grafana || true
                    docker run -d --name grafana --network wanderwise-net -p 3000:3000 -v grafana-storage:/var/lib/grafana grafana/grafana
                    
                    echo "--- Deployment Diagnostics ---"
                    docker ps --filter "network=wanderwise-net"
                    '''
                }
            }
        }
    }
}