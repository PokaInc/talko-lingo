WEBSITE_SOURCE_TEMPLATE_PATH = cloudformation/website/website.yml
GENERATED_WEBSITE_TEMPLATE_ABSOLUTE_PATH = $(shell pwd)/dist/$(WEBSITE_SOURCE_TEMPLATE_PATH)

TALKO_LINGO_SOURCE_TEMPLATE_PATH = cloudformation/talko-lingo/talko-lingo.yml
GENERATED_TALKO_LINGO_TEMPLATE_ABSOLUTE_PATH = $(shell pwd)/dist/$(TALKO_LINGO_SOURCE_TEMPLATE_PATH)

BUCKET_NAME=talko-lingo-`aws sts get-caller-identity --output text --query 'Account'`-$${AWS_DEFAULT_REGION:-`aws configure get region`}

# Check if variable has been defined, otherwise print custom error message
check_defined = \
	$(strip $(foreach 1,$1, \
		$(call __check_defined,$1,$(strip $(value 2)))))
__check_defined = \
	$(if $(value $1),, \
		$(error Undefined $1$(if $2, ($2))))

check-bucket:
	@aws s3api head-bucket --bucket $(BUCKET_NAME) &> /dev/null || aws s3 mb s3://$(BUCKET_NAME)

package-talko-lingo: check-bucket
	@./package_local_lambdas.sh
	@aws cloudformation package --template-file $(TALKO_LINGO_SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/talkolingo --output-template-file $(GENERATED_TALKO_LINGO_TEMPLATE_ABSOLUTE_PATH)

deploy-talko-lingo: package-talko-lingo
	@aws cloudformation deploy --template-file $(GENERATED_TALKO_LINGO_TEMPLATE_ABSOLUTE_PATH) --stack-name TalkoLingo --capabilities CAPABILITY_IAM

deploy-lambdas-on-local-devices:
	aws

package-website: check-bucket
	@aws cloudformation package --template-file $(WEBSITE_SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/talkolingo --output-template-file $(GENERATED_WEBSITE_TEMPLATE_ABSOLUTE_PATH)

deploy-website: package-website
	@aws cloudformation deploy --template-file $(GENERATED_WEBSITE_TEMPLATE_ABSOLUTE_PATH) --stack-name TalkoLingo-Website --parameter-overrides DomainName=$(DOMAIN_NAME) Certificate=$(CERTIFICATE) HostedZoneId=$(HOSTED_ZONE)
	@aws s3 sync website/ s3://www.$(DOMAIN_NAME) --exclude "*/.DS_Store"

update-website:
	@aws s3 sync website/ s3://www.$(DOMAIN_NAME) --exclude "*/.DS_Store"
