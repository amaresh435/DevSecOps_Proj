pipeline {
    agent any
    tools { 
        maven 'maven-3.8.6' 
    }
    environment{
        VERSION = "${env.BUILD_ID}"
    }
    stages {
        stage('Checkout git') {
            steps {
               git branch: 'sonar', url: 'https://github.com/amaresh435/java-web-app'
            }
        }
        
        stage ('Basic standard check') {
            steps {
                sh '''
                  GIT_COMMIT=$(git rev-parse HEAD)
                  echo $GIT_COMMIT
                  PULL_REQUEST_ID=`git log -1 | sed -n '5p' |awk  '{ print $NF }'|sed 's/[^0-9]*//g'`
                  echo $PULL_REQUEST_ID
                  if [ ${CHANGE_ID} ]; then
                        python3 .cicd/scripts/github_api_call.py -o DataWareHouseOrg -t ${PASSWORD} -r ${GIT_REPO_NAME} -l ${CHANGE_ID} -c add_labels -e "{\\"labels\\": [\\"in_development\\"]}"
                  fi
                  #Getting all files from all commits in Open PR 
                  if [ ! -z $CHANGE_ID ]; then 
                      python3 .cicd/scripts/github_api_call.py -o DataWareHouseOrg  -t ${PASSWORD} -r ${GIT_REPO_NAME} -l ${CHANGE_ID} -c fetch_files_from_pr -e '{"message": "Adding message"}'
                      cat pr_file_list.txt
                      cp pr_file_list.txt ${WORKSPACE}/change_files_01_RT.txt
                  else
                      GIT_COMMIT=$(git rev-parse HEAD)
                      echo -e "Commit ID: $GIT_COMMIT"
                      git show $COMMIT | grep "^diff" | awk -F ' ' '{print $3}' |cut -d '/' -f 2- > ${WORKSPACE}/change_files_01_RT.txt
                      git show $COMMIT | grep "^diff" | awk -F ' ' '{print $4}' |cut -d '/' -f 2- >> ${WORKSPACE}/change_files_01_RT.txt
                  fi
                  #checking for unique files for combining all commits
                  if [ -s ${WORKSPACE}/change_files_01_RT.txt ]; then  
                      sort -u ${WORKSPACE}/change_files_01_RT.txt > ${WORKSPACE}/change_all_files_RT.txt
                  fi
                  #Checking for file exists OR Not, ignoring the removed files
                  while read line; do
                      if [ -s $line ] ; then
                          echo "$line" >> ${WORKSPACE}/change_files_RT.txt
                      fi
                  done < ${WORKSPACE}/change_all_files_RT.txt
                  echo "read all files changed in this commit"
                  if [ -s ${WORKSPACE}/change_files_RT.txt ] ; then
                      cat ${WORKSPACE}/change_files_RT.txt
                  fi
                  if grep -i -E 'serviceA/' ${WORKSPACE}/change_files_RT.txt > ${WORKSPACE}/serviceA.txt ; then
                      cat ${WORKSPACE}/adhoc_change_files_RT_plugin_check.txt
                  fi
                  if grep -i -E 'serviceB/' ${WORKSPACE}/change_files_RT.txt > ${WORKSPACE}/serviceB.txt ; then
                      cat ${WORKSPACE}/adhoc_change_files_RT_dags_check.txt
                  fi
                  if grep -i -E 'serviceC/' ${WORKSPACE}/change_files_RT.txt > ${WORKSPACE}/serviceC.txt ; then
                      cat ${WORKSPACE}/No_of_Changed_files_in_sp_n_create_tb.txt
                  fi
                  No_of_Changed_files_in_plugins_dir=`wc -l < ${WORKSPACE}/adhoc_change_files_RT_plugin_check.txt`
                  No_of_Changed_files_in_dags_dir=`wc -l < ${WORKSPACE}/adhoc_change_files_RT_dags_check.txt`
                  if grep -i -E 'stored_procedures/mti/|adhoc/mti/create_table/' ${WORKSPACE}/change_files_RT.txt >> ${WORKSPACE}/No_of_Changed_files_in_sp_n_create_tb_mti.txt ; then
                      cat ${WORKSPACE}/No_of_Changed_files_in_sp_n_create_tb_mti.txt
                  fi
                  if grep -i -E 'stored_procedures/dw/|stored_procedures/drop_procedures/|stored_procedures/mti/' ${WORKSPACE}/change_files_RT.txt > ${WORKSPACE}/only_sp_files_in_pr_dw_n_mti.txt ; then
                      cat ${WORKSPACE}/only_sp_files_in_pr_dw_n_mti.txt
                      while read sp_file_each_line; do
                          echo $sp_file_each_line > ${WORKSPACE}/read_each_file_path.txt
                          if grep -i -E 'stored_procedures/.*.dw_sql' ${WORKSPACE}/read_each_file_path.txt ; then
                          echo "all SP file having correct file extension dw_sql, Good to Go"
                          else
                          echo "$sp_file_each_line: this file has wrong sp extension type, hence run test fails" >> ${WORKSPACE}/sp_wrong_file_extension_capture.txt
                          fi
                      done < ${WORKSPACE}/only_sp_files_in_pr_dw_n_mti.txt
                      if [ -s ${WORKSPACE}/sp_wrong_file_extension_capture.txt ] ; then
                          sp_wrong_file_extension_capture=${WORKSPACE}/sp_wrong_file_extension_capture.txt
                          echo $sp_wrong_file_extension_capture
                          python3 .cicd/scripts/github_api_call.py -o DataWareHouseOrg  -t ${PASSWORD} -r ${GIT_REPO_NAME} -l ${CHANGE_ID} -c add_comment -e '{"message": "Automatted Github Message:\\nStored Procedure files has incorrect file extension. [Stored Procedure standard document.](https://github.bedbath.com/DataWarehouseOrg/dw_airflow/blob/develop/stored_procedures/README.md)", "filename": "'"${sp_wrong_file_extension_capture}"'"}'
                          exit 1
                      fi
                  fi
                '''
            }
            
        }
        
        stage('Build & JUnit Test'){
            steps{
                   withSonarQubeEnv(installationName: 'sonarqube') {
                        sh 'mvn clean org.sonarsource.scanner.maven:sonar-maven-plugin:3.9.0.2155:sonar'
                    }
            }
            timeout(time: 1, unit: 'HOURS') {
                def qg = waitForQualityGate()
                if (qg.status != 'OK') {
                    error "Pipeline aborted due to quality gate failure: ${qg.status}"
                }
            }
            post {
                 success {
                      junit 'target/surefire-reports/**/*.xml'
                  }   
            }
        }
        stage('Building Docker Image'){
            steps{
                sh '''
                docker build -t 34.125.214.226:8083/springapp:$VERSION .
                sudo docker images
                '''
            }
        }
        stage('Image Scanning Trivy'){
            steps{
               sh 'sudo trivy image amaresh435/devsecops-demo:$VERSION > $WORKSPACE/trivy-image-scan/trivy-image-scan-$VERSION.txt'   
            }
        }       
        
        stage ('Uploading Reports to Cloud Storage'){
            steps{
                   withCredentials(credentialsId: 'cloud-storage-access', variable: 'CLOUD_CREDS') {
                   sh '''
                   gcloud version
                   gcloud auth activate-service-account --key-file="$CLOUD_CREDS"
                   gsutil cp -r $WORKSPACE/trivy-image-scan/trivy-image-scan-$VERSION.txt gs://devsecops-reports
                   gsutil ls gs://devsecops-reports
                   grep "critical" $WORKSPACE/trivy-image-scan/trivy-image-scan-$VERSION.txt > docker_image_scan_error_report.txt
                   if [ -s ${WORKSPACE}/docker_image_scan_error_report.txt ] ; then
                        error_info=${WORKSPACE}/docker_image_scan_error_report.txt
                        echo $error_info
                        python3 .cicd/scripts/github_api_call.py -o DataWareHouseOrg  -t ${PASSWORD} -r ${GIT_REPO_NAME} -l ${CHANGE_ID} -c add_comment -e '{"message": "Automatted Github Message:\\nDocker scan error report at gs://devsecops-reports/$WORKSPACE/trivy-image-scan/trivy-image-scan-$VERSION.txt. [Stored Procedure standard document.](https://URL)", "filename": "'"${error_info}"'"}'
                        exit 1
                    fi
                   '''
                }
            }
        }
        stage("docker push to Nexus"){
            steps{
                script{
                    withCredentials([string(credentialsId: 'docker_pass', variable: 'docker_password')]) {
                             sh '''
                                docker login -u admin -p $docker_password $nexus_ip 
                                docker push  $nexus_ip/springapp:${VERSION}
                                docker rmi $nexus_ip/springapp:${VERSION}
                            '''
                    }
                }
            }
        }
        stage('Pushing Docker Image into Docker Hub'){
            steps{
                withCredentials(credentialsId: 'dockerhub-id', variable: 'DOCKERHUB_PASSWORD') {
                sh '''
                sudo docker login -u amaresh435 -p $DOCKERHUB_PASSWORD
                sudo docker push logicopslab/devsecops-demo:$BUILD_ID
                '''
               }
            }
        } 
        stage('Cleaning up DockerImage'){
            steps{
                sh 'sudo docker rmi amaresh435/devsecops-demo:$BUILD_ID'
            }
        }
        stage('indentifying misconfigs using datree in helm charts'){
            steps{
                script{
                    dir('kubernetes/') {
                        withEnv(credentialsId: 'cloud-storage-access', variable: 'CLOUD_CREDS'){
                              sh '''
                                helm datree test myapp/ > misconfigs_error.txt
                                if [ -s ${WORKSPACE}/misconfigs_error.txt ] ; then
                                    misconfig_error_info=${WORKSPACE}/misconfigs_error.txt
                                    echo $misconfig_error_info
                                    python3 .cicd/scripts/github_api_call.py -o DataWareHouseOrg  -t ${PASSWORD} -r ${GIT_REPO_NAME} -l ${CHANGE_ID} -c add_comment -e '{"message": "Automatted Github Message:\\nDocker scan error report at gs://devsecops-reports/$WORKSPACE/trivy-image-scan/trivy-image-scan-$VERSION.txt. [Stored Procedure standard document.](https://URL)", "filename": "'"${misconfig_error_info}"'"}'
                                    exit 1
                                fi
                              '''
                        }
                    }
                }
            }
        }
        stage("pushing the helm charts to nexus"){
            steps{
                script{
                    withCredentials([string(credentialsId: 'docker_id', variable: 'docker_password')]) {
                          dir('kubernetes/') {
                             sh '''
                                 helmversion=$( helm show chart myapp | grep version | cut -d: -f 2 | tr -d ' ')
                                 tar -czvf  myapp-${helmversion}.tgz myapp/
                                 curl -u admin:$docker_password http://nexus_ip/repository/helm-hosted/ --upload-file myapp-${helmversion}.tgz -v
                            '''
                          }
                    }
                }
            }
        }
        
        stage("Deploy to Develop") {
            if (env.BRANCH_NAME == "develop"){
                serial( 
                    "manual approval"{
                    script{
                            timeout(10) {
                                mail bcc: '', body: "<br>Project: ${env.JOB_NAME} <br>Build Number: ${env.BUILD_NUMBER} <br> Go to build url and approve the deployment request <br> URL de build: ${env.BUILD_URL}", cc: '', charset: 'UTF-8', from: '', mimeType: 'text/html', replyTo: '', subject: "${currentBuild.result} CI: Project name -> ${env.JOB_NAME}", to: "amareshguligoudar@gmail.com";  
                                input(id: "Deploy Gate", message: "Deploy ${params.project_name}?", ok: 'Deploy')
                            }
                        }
                    }
                    "Deploying application on k8s cluster" {
                    steps {
                        script{
                            withCredentials([kubeconfigFile(credentialsId: 'kubernetes-config', variable: 'KUBECONFIG')]) {
                                    dir('kubernetes/') {
                                    sh '
                                        gcloud config set project dw-bq-data-d00
                                        gcloud config set account prod-dw-jenkins-batch0001@dw-bq-data-d00.iam.gserviceaccount.com --quiet
                                        COMMAND='gcloud'
                                        LOCATION='--location us-east4'
                                        gcloud config configurations create devdwjenkinsd00
                                        export CLOUDSDK_ACTIVE_CONFIG_NAME=devdwjenkinsd00
                                        gcloud auth activate-service-account --key-file="$KUBECONFIG"
                                        gcloud config set project 'dw-bq-data-p00'
                                        gcloud config configurations activate devdwjenkinsd00
                                        helm upgrade --install --set image.repository="nexus_ip/springapp" --set image.tag="${VERSION}" myjavaapp myapp/ ' 
                                    '''
                                    }
                                }
                        }
                    }
                )
            }
        }

          stage("Deploy to Release") {
            if (env.BRANCH_NAME == "release"){
                serial( 
                    "manual approval"{
                    script{
                            timeout(10) {
                                mail bcc: '', body: "<br>Project: ${env.JOB_NAME} <br>Build Number: ${env.BUILD_NUMBER} <br> Go to build url and approve the deployment request <br> URL de build: ${env.BUILD_URL}", cc: '', charset: 'UTF-8', from: '', mimeType: 'text/html', replyTo: '', subject: "${currentBuild.result} CI: Project name -> ${env.JOB_NAME}", to: "amareshguligoudar@gmail.com";  
                                input(id: "Deploy Gate", message: "Deploy ${params.project_name}?", ok: 'Deploy')
                            }
                        }
                    }
                    "Deploying application on k8s cluster" {
                    steps {
                        script{
                            withCredentials([kubeconfigFile(credentialsId: 'kubernetes-config', variable: 'KUBECONFIG')]) {
                                    dir('kubernetes/') {
                                    sh '
                                        gcloud config set project dw-bq-data-p00
                                        gcloud config set account prod-dw-jenkins-batch0001@dw-bq-data-d00.iam.gserviceaccount.com --quiet
                                        COMMAND='gcloud'
                                        LOCATION='--location us-east4'
                                        gcloud config configurations create proddwjenkinsd00
                                        export CLOUDSDK_ACTIVE_CONFIG_NAME=proddwjenkinsd00
                                        gcloud auth activate-service-account --key-file="$KUBECONFIG"
                                        gcloud config set project 'dw-bq-data-p00'
                                        gcloud config configurations activate proddwjenkinsd00
                                        helm upgrade --install --set image.repository="nexus_ip/springapp" --set image.tag="${VERSION}" myjavaapp myapp/ ' 
                                    '''
                                    }
                                }
                        }
                    }
                )
            }
        }
    }
  }
