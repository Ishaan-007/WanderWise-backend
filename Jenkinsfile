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
                
                # Move the coverage report to the root so Sonar can see it
                docker cp test-run:/app/coverage.xml .
                docker rm test-run
                '''
            }
        }

        stage('Static Code Analysis') {
            steps {
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_KEY')]) {
                    sh """
                    # 1. Create a clean properties file
                    echo "sonar.projectKey=Wanderwise-Backend" > sonar-project.properties
                    echo "sonar.sources=app" >> sonar-project.properties
                    echo "sonar.host.url=https://cascade-comic-shoplift.ngrok-free.dev" >> sonar-project.properties
                    echo "sonar.login=${SONAR_KEY}" >> sonar-project.properties
                    echo "sonar.python.version=3" >> sonar-project.properties
                    echo "sonar.scm.disabled=true" >> sonar-project.properties
                    
                    # 2. Link your Pytest results to SonarQube
                    echo "sonar.python.coverage.reportPaths=coverage.xml" >> sonar-project.properties

                    # 3. Run the scanner using the properties file instead of long flags
                    docker run --rm \
                    -v \$(pwd):/usr/src \
                    -e SONAR_SCANNER_OPTS="-Xmx512m" \
                    sonarsource/sonar-scanner-cli
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