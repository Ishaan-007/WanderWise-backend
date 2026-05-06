provider "aws" {
  region = "ap-south-1"
}

resource "aws_key_pair" "deployer" {
  key_name   = "wanderwise-keyx"
  # Safe to push the public key to GitHub, NEVER push the private key
  public_key = file("wanderwise-keyx.pub") 
}

resource "aws_security_group" "wanderwise_sg" {
  name = "wanderwise_sg"

  # SSH Access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Jenkins CI/CD
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FastAPI Application
  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Prometheus Observability
  ingress {
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Grafana Dashboards
  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SonarQube (Required if you ever move SonarQube from localhost to AWS)
  ingress {
    from_port   = 9000
    to_port     = 9000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_instance" "wanderwise" {
  ami           = "ami-0f5ee92e2d63afc18" # Ubuntu (Mumbai region)
  instance_type = "t3.micro"

  key_name        = aws_key_pair.deployer.key_name
  security_groups = [aws_security_group.wanderwise_sg.name]

  tags = {
    Name = "WanderWise-DevOps"
  }
}

output "public_ip" {
  value = aws_instance.wanderwise.public_ip
}

# Automatically generate the Ansible inventory file with the new IP
resource "local_file" "ansible_inventory" {
  content = <<-EOF
    [aws]
    ${aws_instance.wanderwise.public_ip} ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/wanderwise-keyx
    EOF
  
  # This saves the file directly into your ansible folder!
  filename = "../ansible/inventory.ini"
}