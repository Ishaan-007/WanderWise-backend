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

                # Notice the added -e MONGO_URI flag with a dummy localhost connection!
                docker run --name test-run \
                -e MONGO_URI="mongodb://localhost:27017/test_database" \
                wanderwise-backend:latest \
                bash -c "
                python -m pytest --cov=app --cov-report=xml tests/
                "

                docker cp test-run:/app/coverage.xml .
                docker rm test-run
                '''
            }
        }

        stage('Static Code Analysis') {
            steps {
                withCredentials([string(credentialsId: 'SONAR_TOKEN', variable: 'SONAR_KEY')]) {
                    sh """
                    docker run --rm \
                    -v \$(pwd):/usr/src \
                    sonarsource/sonar-scanner-cli \
                    -Dsonar.projectKey=Wanderwise-Backend \
                    -Dsonar.sources=app \
                    -Dsonar.exclusions=**/__pycache__/** \
                    -Dsonar.host.url=https://cascade-comic-shoplift.ngrok-free.dev \
                    -Dsonar.login=${SONAR_KEY}
                    """
                }
            }
        }

        stage('Deploy Observability Stack') {
            steps {
                // We wrap the deployment steps in this block to securely grab the secret
                withCredentials([string(credentialsId: 'MONGO_URI_SECRET', variable: 'DB_URI')]) {
                    sh '''
                    # 1. Create a shared network
                    docker network create wanderwise-net || true

                    # 2. Start the WanderWise App (Now with the secure database URI!)
                    docker rm -f wanderwise-app || true
                    
                    # Notice we use double quotes (") here so Jenkins can inject the $DB_URI variable
                    docker run -d \
                      --name wanderwise-app \
                      --network wanderwise-net \
                      -p 8000:8000 \
                      -e MONGO_URI="$DB_URI" \
                      wanderwise-backend:latest

                    # 3. Create a temporary config file on the host machine
                    cat <<EOF > prometheus_temp.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'wanderwise-backend'
    static_configs:
      - targets: ['wanderwise-app:8000']
EOF

                    # 4. Start Prometheus
                    docker rm -f prometheus || true
                    docker run -d \
                      --name prometheus \
                      --network wanderwise-net \
                      -p 9090:9090 \
                      prom/prometheus
                      
                    sleep 2
                    docker cp prometheus_temp.yml prometheus:/etc/prometheus/prometheus.yml
                    docker restart prometheus

                    # 5. Start Grafana (Now with persistent storage!)
                    docker volume create grafana-storage || true
                    docker rm -f grafana || true
                    
                    docker run -d \
                      --name grafana \
                      --network wanderwise-net \
                      -p 3000:3000 \
                      -v grafana-storage:/var/lib/grafana \
                      grafana/grafana
                    '''
                }
            }
        }
    }
}