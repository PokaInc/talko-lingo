WEBSITE_SOURCE_TEMPLATE_PATH = cloudformation/website/website.yml
GENERATED_WEBSITE_TEMPLATE_ABSOLUTE_PATH = $(shell pwd)/dist/$(WEBSITE_SOURCE_TEMPLATE_PATH)

TRANSCRIBE_SOURCE_TEMPLATE_PATH = cloudformation/transcribe/transcribe.yml
GENERATED_TRANSCRIBE_TEMPLATE_ABSOLUTE_PATH = $(shell pwd)/dist/$(TRANSCRIBE_SOURCE_TEMPLATE_PATH)

package-website: export BUCKET_NAME=cf-template-`aws sts get-caller-identity --output text --query 'Account'`-`aws configure get region`
package-website:
	aws cloudformation package --template-file $(WEBSITE_SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/talkolingo --output-template-file $(GENERATED_WEBSITE_TEMPLATE_ABSOLUTE_PATH)

package-transcribe: export BUCKET_NAME=cf-template-`aws sts get-caller-identity --output text --query 'Account'`-`aws configure get region`
package-transcribe:
	aws cloudformation package --template-file $(TRANSCRIBE_SOURCE_TEMPLATE_PATH) --s3-bucket $(BUCKET_NAME) --s3-prefix cloudformation/talkolingo --output-template-file $(GENERATED_TRANSCRIBE_TEMPLATE_ABSOLUTE_PATH)

transcribe: package-transcribe
	aws cloudformation deploy --template-file $(GENERATED_TRANSCRIBE_TEMPLATE_ABSOLUTE_PATH) --stack-name TalkoLingo-Transcribe

website: package-website
	aws cloudformation deploy --template-file $(GENERATED_WEBSITE_TEMPLATE_ABSOLUTE_PATH) --stack-name TalkoLingo-Website --parameter-overrides DomainName=$(DOMAIN_NAME) Certificate=$(CERTIFICATE) HostedZoneId=$(HOSTED_ZONE)
	aws s3 sync website/ s3://www.$(DOMAIN_NAME) --exclude "*/.DS_Store"

update-website:
	aws s3 sync website/ s3://www.$(DOMAIN_NAME) --exclude "*/.DS_Store"
