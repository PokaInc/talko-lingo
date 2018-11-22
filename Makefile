RASPBERRY_PI_CREDENTIALS_TEMPLATE_PATH = cloudformation/talko-lingo/raspberry-pi-credentials.yml

WEBSITE_SOURCE_TEMPLATE_PATH = cloudformation/website/website.yml
GENERATED_WEBSITE_TEMPLATE_ABSOLUTE_PATH = $(shell pwd)/dist/$(WEBSITE_SOURCE_TEMPLATE_PATH)

TALKO_LINGO_SOURCE_TEMPLATE_PATH = cloudformation/talko-lingo/talko-lingo.yml
GENERATED_TALKO_LINGO_TEMPLATE_ABSOLUTE_PATH = $(shell pwd)/dist/$(TALKO_LINGO_SOURCE_TEMPLATE_PATH)

TALKO_LINGO_STACK_NAME=TalkoLingo
RASPBERRY_PI_CREDENTIALS_STACK_NAME=RaspberryPiCredentials

BUCKET_NAME=talko-lingo-`aws sts get-caller-identity --output text --query 'Account'`-$${AWS_DEFAULT_REGION:-`aws configure get region`}

AWS_REGION=$(shell aws configure get region)
WEB_UI_BUCKET_NAME=$(shell aws cloudformation describe-stacks --stack-name $(TALKO_LINGO_STACK_NAME) --query "Stacks[0].Outputs[?OutputKey=='WebsiteBucketName'].OutputValue" --output text --region $(AWS_REGION))

# Check if variable has been defined, otherwise print custom error message
check_defined = \
	$(strip $(foreach 1,$1, \
		$(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
	$(if $(value $1),, \
		$(error Undefined $1$(if $2, ($2))))

build-web-ui:
	cd src/web_ui; npm install
	cd src/web_ui/node_modules/aws-iot-device-sdk; npm run-script browserize
	rsync --update src/web_ui/index.js src/web_ui/dist/
	rsync --update src/web_ui/index.html src/web_ui/dist/
	rsync --update src/web_ui/index.css src/web_ui/dist/
	rsync --update src/web_ui/node_modules/aws-iot-device-sdk/browser/aws-iot-sdk-browser-bundle.js src/web_ui/dist/

deploy-web-ui: build-web-ui
	aws s3 sync src/web_ui/dist s3://$(WEB_UI_BUCKET_NAME)

check-bucket:
	@aws s3api head-bucket --bucket $(BUCKET_NAME) &> /dev/null || aws s3 mb s3://$(BUCKET_NAME)

download_transcribe_preview_jar:
	aws s3 sync s3://talko-lingo-jars src/cloud/english_transcribe_function/jars/

build_english_transcribe_function: download_transcribe_preview_jar
	cd src/cloud/english_transcribe_function; ./gradlew build

raspberry-pi-credentials:
	@./create_raspberry_pi_credentials.sh $(RASPBERRY_PI_CREDENTIALS_TEMPLATE_PATH) $(RASPBERRY_PI_CREDENTIALS_STACK_NAME) $(TALKO_LINGO_STACK_NAME)

package-talko-lingo: check-bucket build_english_transcribe_function
	@./package_local_lambdas.sh
	docker run -v `pwd`/src/cloud/s3_event_handlers/:/dependencies/ python:3.6 pip install -t /dependencies/ google-cloud-speech
	@aws cloudformation package --template-file $(TALKO_LINGO_SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/talkolingo --output-template-file $(GENERATED_TALKO_LINGO_TEMPLATE_ABSOLUTE_PATH)

deploy-talko-lingo: package-talko-lingo
	@aws cloudformation deploy --template-file $(GENERATED_TALKO_LINGO_TEMPLATE_ABSOLUTE_PATH) --stack-name $(TALKO_LINGO_STACK_NAME) --capabilities CAPABILITY_IAM

deploy-lambdas-on-local-devices:
	aws

package-website: check-bucket
	@aws cloudformation package --template-file $(WEBSITE_SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/talkolingo --output-template-file $(GENERATED_WEBSITE_TEMPLATE_ABSOLUTE_PATH)

deploy-website: package-website
	@aws cloudformation deploy --template-file $(GENERATED_WEBSITE_TEMPLATE_ABSOLUTE_PATH) --stack-name TalkoLingo-Website --parameter-overrides DomainName=$(DOMAIN_NAME) Certificate=$(CERTIFICATE) HostedZoneId=$(HOSTED_ZONE)
	@aws s3 sync website/ s3://www.$(DOMAIN_NAME) --exclude "*/.DS_Store"

update-website:
	@aws s3 sync website/ s3://www.$(DOMAIN_NAME) --exclude "*/.DS_Store"

install-raspberry-pi-service:
	@sudo systemctl enable $(shell pwd)/tx.service
	@sudo systemctl enable $(shell pwd)/rx.service
	@sudo systemctl start tx.service
	@sudo systemctl start rx.service
