import boto3
from talko_lingo.utils.job_id import extract_input_output_lang_from_job_id


def translate(text_to_translate, job_id):
    input_lang, output_lang = extract_input_output_lang_from_job_id(job_id)

    # we're only interested in the first part of the code, e.g. en-US becomes en, fr-CA becomes fr
    input_lang = input_lang.split('-')[0]
    output_lang = output_lang.split('-')[0]

    print('Translating job ' + job_id)
    if input_lang != output_lang:
        translate_client = boto3.client('translate')
        translated_text = translate_client.translate_text(
            Text=text_to_translate,
            SourceLanguageCode=input_lang,
            TargetLanguageCode=output_lang
        )['TranslatedText']
        print('Translated text: ' + translated_text)
    else:
        translated_text = text_to_translate
        print('Same input/output language, not translating')

    return translated_text
